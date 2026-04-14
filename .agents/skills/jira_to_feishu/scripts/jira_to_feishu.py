import os
import sys
import re
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
# Jira配置
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

# 飞书配置
FEISHU_APP_ID = "cli_a95276171379dbda"
FEISHU_APP_SECRET = "weWRebXG3hpUFdHWVTtAKjDY3Vrleyiw"
FEISHU_DOC_TOKEN = "shtcnEdGsdXmuVKvxVGAOmpXKwf"
FEISHU_SHEET_ID = "fLpHwq"

# Jira筛选器ID
JIRA_FILTER_ID_1 = "20815"  # 原任务筛选器
JIRA_FILTER_ID_2 = "20818"  # 故障筛选器
# ----------------------------------------------------------

try:
    # 检查必要配置
    if not all([JIRA_BASE_URL, JIRA_TOKEN, FEISHU_APP_ID, FEISHU_APP_SECRET]):
        print("[ERROR] 缺少必要配置，请检查脚本里的 FEISHU_APP_ID 和 FEISHU_APP_SECRET 是否填写正确")
        sys.exit(1)

    # -------------------------- 1. 获取飞书 tenant_access_token --------------------------
    def get_feishu_token():
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": FEISHU_APP_ID,
            "app_secret": FEISHU_APP_SECRET
        }, timeout=30)
        if resp.status_code != 200:
            print(f"[ERROR] 获取飞书token失败：HTTP {resp.status_code} 响应：{resp.text}")
            sys.exit(1)
        data = resp.json()
        if data.get("code") != 0:
            print(f"[ERROR] 获取飞书token返回错误：code={data.get('code')} msg={data.get('msg')}")
            sys.exit(1)
        return data["tenant_access_token"]

    # -------------------------- 2. 从Jira筛选器拉取数据 --------------------------
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Accept": "application/json",
    }

    def get_issues_from_filter(filter_id, issue_type_override=None):
        """从Jira筛选器获取数据"""
        # 首先获取筛选器的JQL
        filter_url = f"{JIRA_BASE_URL}/rest/api/2/filter/{filter_id}"
        filter_resp = requests.get(filter_url, headers=headers, timeout=60)
        if filter_resp.status_code != 200:
            print(f"[ERROR] 获取筛选器失败：HTTP {filter_resp.status_code} 响应：{filter_resp.text}")
            return []
        filter_data = filter_resp.json()
        jql = filter_data.get("jql", "")
        
        if not jql:
            print(f"[ERROR] 无法获取筛选器 {filter_id} 的JQL")
            return []
        
        # 使用JQL查询数据
        search_url = f"{JIRA_BASE_URL}/rest/api/2/search"
        params = {
            "jql": jql,
            "maxResults": 1000,
            "fields": "summary,status,assignee,issuetype,fixVersions,updated,reporter"
        }
        
        search_resp = requests.get(search_url, headers=headers, params=params, timeout=60)
        if search_resp.status_code != 200:
            print(f"[ERROR] 查询Jira数据失败：HTTP {search_resp.status_code} 响应：{search_resp.text}")
            return []
        
        search_data = search_resp.json()
        issues = search_data.get("issues", [])
        
        # 如果指定了任务类型覆盖，则修改任务类型
        if issue_type_override:
            for issue in issues:
                fields = issue.get("fields", {})
                if fields.get("issuetype"):
                    fields["issuetype"]["name"] = issue_type_override
        
        print(f"[INFO] 从筛选器 {filter_id} 拉取完成，共 {len(issues)} 条任务")
        return issues

    # 从两个筛选器获取数据
    print("[INFO] 正在拉取Jira数据...")
    issues1 = get_issues_from_filter(JIRA_FILTER_ID_1)
    issues2 = get_issues_from_filter(JIRA_FILTER_ID_2, issue_type_override="故障")
    
    # 合并数据
    issues = issues1 + issues2
    print(f"[INFO] 合并完成，共 {len(issues)} 条原始任务")

    # -------------------------- 3. 数据处理、排序、过滤 --------------------------
    def get_sort_key(version_name):
        """从版本名称中提取日期作为排序键"""
        # 尝试匹配日期格式，如 0429、0501 等
        matches = re.findall(r'(\d{4})', version_name.strip())
        if matches:
            return int(matches[-1])
        
        # 尝试匹配其他可能的日期格式
        # 例如：20240429、240429 等
        matches2 = re.findall(r'(\d{6,8})', version_name.strip())
        if matches2:
            # 取后4位作为排序键
            return int(matches2[-1][-4:])
        
        return 0

    processed = []
    for issue in issues:
        fields = issue.get("fields", {})
        fix_versions = fields.get("fixVersions") or []
        max_key = 0
        version_text = ""
        if fix_versions:
            for v in fix_versions:
                name = v.get("name", "")
                key = get_sort_key(name)
                if key > max_key:
                    max_key = key
                    version_text = name
            if not version_text:
                version_text = ", ".join(v.get("name", "") for v in fix_versions)
        if "日常资源版本" in version_text:
            continue
        updated_str = fields.get("updated", "")
        updated_ts = 0
        if updated_str:
            try:
                from dateutil.parser import parse
                updated_ts = parse(updated_str).timestamp()
            except:
                pass
        issue_key = issue.get("key", "")
        issue_url = f"{JIRA_BASE_URL}/browse/{issue_key}" if JIRA_BASE_URL and issue_key else ""
        
        # 修改任务类型映射
        issue_type = (fields.get("issuetype") or {}).get("name", "")
        if issue_type in ["故事", "任务"]:
            issue_type = "功能测试"
        elif issue_type == "故障":
            issue_type = "缺陷验收"
        
        # 修改执行人字段为报告人
        reporter = (fields.get("reporter") or {}).get("displayName", "未分配")
        
        processed.append({
            "version_key": max_key,
            "updated_ts": updated_ts,
            "version": version_text,
            "summary": fields.get("summary", ""),
            "issue_key": issue_key,
            "issue_url": issue_url,
            "issue_type": issue_type,
            "assignee": reporter,
            "status": (fields.get("status") or {}).get("name", "")
        })
    # 定义任务类型优先级
    def get_issue_type_priority(issue_type):
        if issue_type == "功能测试":
            return 0  # 优先级高
        elif issue_type == "缺陷验收":
            return 1  # 优先级低
        else:
            return 2  # 其他类型
    
    # 排序：首先按版本字段日期由远到近（升序），然后按任务类型优先级（功能测试>缺陷验收）
    processed.sort(key=lambda x: (x["version_key"], get_issue_type_priority(x["issue_type"])))
    # 修改日期格式，使用简单的字符串格式，不需要公式
    today = datetime.now().strftime("%m月%d日")
    print(f"[INFO] 处理完成，过滤后共 {len(processed)} 条有效任务")

    # -------------------------- 4. 追加写入飞书表格 --------------------------
    print("[INFO] 正在获取飞书访问凭证...")
    feishu_token = get_feishu_token()

    # 先查询当前已有行数，定位到末尾
    print("[INFO] 查询表格当前行数...")
    query_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values/{FEISHU_SHEET_ID}!A:A"
    query_resp = requests.get(query_url, headers={"Authorization": f"Bearer {feishu_token}"}, timeout=30)
    if query_resp.status_code != 200:
        print(f"[ERROR] 查询表格行数失败：HTTP {query_resp.status_code} {query_resp.text}")
        sys.exit(1)
    query_data = query_resp.json()
    if query_data.get("code") != 0:
        print(f"[ERROR] 查询表格行数返回错误：code={query_data.get('code')} msg={query_data.get('msg')}")
        sys.exit(1)

    # 计算追加位置
    values = query_data["data"].get("values", [])
    start_row = len(values) + 1
    
    # 构造写入数据
    # 先写入标题行
    write_rows = []
    write_rows.append([f"【{today} Jira任务整理】", "", "", "", "", ""])
    write_rows.append(["日期", "版本", "任务类型", "任务描述", "执行人", "任务状态"])
    
    # 写入数据行，直接使用 URL，飞书表格会自动识别为蓝色可点击链接
    for item in processed:
        if item.get("issue_url"):
            # 直接写入 URL，飞书表格会自动识别为蓝色可点击链接
            # 格式：任务摘要 (URL)
            summary_with_link = f"{item['summary']} ({item['issue_url']})"
        else:
            # 如果没有URL，显示普通文本
            summary_with_link = item["summary"]
        
        # 只显示版本名，不添加超链接
        version_with_link = item["version"]
        
        write_rows.append([
            today,
            version_with_link,
            item["issue_type"],
            summary_with_link,
            item["assignee"],
            item["status"]
        ])
    write_rows.append(["", "", "", "", "", ""])
    
    # 计算范围
    append_range = f"{FEISHU_SHEET_ID}!A{start_row}:F{start_row + len(write_rows) - 1}"

    print(f"[INFO] 正在写入飞书表格，共 {len(processed)} 条记录...")
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values_append"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json={
            "valueRange": {
                "range": append_range,
                "values": write_rows
            },
            "options": {
                "insertDataOption": "INSERT_ROWS"
            }
        },
        timeout=120
    )
    print(f"[INFO] 飞书接口返回：status={resp.status_code}, body={resp.text}")
    if resp.status_code != 200:
        print(f"[ERROR] 写入飞书失败：HTTP {resp.status_code}")
        sys.exit(1)
    result = resp.json()
    if result.get("code") != 0:
        print(f"[ERROR] 写入飞书返回错误：code={result.get('code')} msg={result.get('msg')}")
        sys.exit(1)
    
    print(f"[INFO] 全部完成！成功追加 {len(processed)} 条记录到飞书表格末尾：")
    print(f"https://bytedance.larkoffice.com/sheets/shtcnEdGsdXmuVKvxVGAOmpXKwf?sheet=fLpHwq")
    print("[INFO] 打开表格后，滚动到最底部就能看到今天最新的数据")


except Exception as e:
    print(f"[ERROR] 发生未知错误：{str(e)}")
    print("[INFO] 错误堆栈：")
    print(traceback.format_exc())
