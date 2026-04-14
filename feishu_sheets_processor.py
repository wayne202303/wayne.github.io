import os
import sys
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
# Jira配置
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://101-jira.bytedance.net")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_FILTER_ID = "20815"  # 筛选器ID

# 飞书配置
FEISHU_APP_ID = "cli_a95276171379dbda"
FEISHU_APP_SECRET = "weWRebXG3hpUFdHWVTtAKjDY3Vrleyiw"
FEISHU_DOC_TOKEN = "shtcnEdGsdXmuVKvxVGAOmpXKwf"
SOURCE_SHEET_ID = "fLpHwq"  # 源表格
EXTRACT_SHEET_ID = "ych5DU"  # 提取后表格
FINAL_SHEET_ID = "KkxL37"  # 最终结果表格
# ----------------------------------------------------------

try:
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

    print("[INFO] 正在获取飞书访问凭证...")
    feishu_token = get_feishu_token()

    # -------------------------- 2. 从 Jira 筛选器拉取数据 --------------------------
    print("[INFO] 正在从 Jira 筛选器拉取数据...")
    if not JIRA_TOKEN:
        print("[ERROR] 缺少 JIRA_TOKEN 配置")
        sys.exit(1)
    
    # 从 Jira 筛选器获取数据
    def get_jira_filter_data(filter_id):
        # 首先获取筛选器的 JQL
        filter_url = f"{JIRA_BASE_URL}/rest/api/2/filter/{filter_id}"
        headers = {
            "Authorization": f"Bearer {JIRA_TOKEN}",
            "Accept": "application/json"
        }
        
        # 获取筛选器信息
        filter_resp = requests.get(filter_url, headers=headers, timeout=60)
        if filter_resp.status_code != 200:
            print(f"[ERROR] 获取筛选器失败：HTTP {filter_resp.status_code} {filter_resp.text}")
            sys.exit(1)
        filter_data = filter_resp.json()
        jql = filter_data.get("jql", "")
        
        if not jql:
            print("[ERROR] 无法获取筛选器的 JQL")
            sys.exit(1)
        
        # 使用 JQL 查询数据
        search_url = f"{JIRA_BASE_URL}/rest/api/2/search"
        params = {
            "jql": jql,
            "maxResults": 1000,
            "fields": "summary,status,assignee,issuetype,fixVersions,updated,key"
        }
        
        search_resp = requests.get(search_url, headers=headers, params=params, timeout=60)
        if search_resp.status_code != 200:
            print(f"[ERROR] 查询 Jira 数据失败：HTTP {search_resp.status_code} {search_resp.text}")
            sys.exit(1)
        search_data = search_resp.json()
        issues = search_data.get("issues", [])
        
        print(f"[INFO] 从 Jira 筛选器获取到 {len(issues)} 条数据")
        return issues
    
    # 获取 Jira 数据
    jira_issues = get_jira_filter_data(JIRA_FILTER_ID)
    
    # 构造表格数据
    source_values = []
    # 添加表头
    source_values.append(["关键字", "概要", "修复版本", "任务类型", "状态", "执行人"])
    
    # 添加数据行
    for issue in jira_issues:
        fields = issue.get("fields", {})
        key = issue.get("key", "")
        summary = fields.get("summary", "")
        fix_versions = fields.get("fixVersions", [])
        version_text = ", ".join(v.get("name", "") for v in fix_versions)
        issue_type = (fields.get("issuetype") or {}).get("name", "")
        status = (fields.get("status") or {}).get("name", "")
        assignee = (fields.get("assignee") or {}).get("displayName", "未分配")
        
        # 直接使用文本，不使用 HYPERLINK 公式
        # 飞书表格会自动识别 URL 并显示为超链接
        source_values.append([key, summary, version_text, issue_type, status, assignee])
    
    # 写入源表格
    print("[INFO] 正在写入源表格...")
    source_range = f"{SOURCE_SHEET_ID}!A1:F{len(source_values)}"
    source_write_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values"
    source_write_resp = requests.put(
        source_write_url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json={
            "valueRange": {
                "range": source_range,
                "values": source_values
            }
        },
        timeout=60
    )
    if source_write_resp.status_code != 200:
        print(f"[ERROR] 写入源表格失败：HTTP {source_write_resp.status_code} {source_write_resp.text}")
        sys.exit(1)
    print("[INFO] 成功写入源表格")
    
    # 尝试使用 v3 API 批量更新设置超链接
    print("[INFO] 正在设置超链接...")
    batch_update_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_DOC_TOKEN}/sheets/{SOURCE_SHEET_ID}/cells/batch_update"
    
    # 构建批量更新请求
    requests_body = {
        "requests": []
    }
    
    # 为关键字和概要列设置超链接
    for row_idx in range(1, len(source_values)):
        # 从 Jira 问题中获取 key
        issue = jira_issues[row_idx - 1]  # 因为 source_values 包含表头，所以索引减 1
        key = issue.get("key", "")
        if not key:
            continue
        
        # 构建超链接 URL
        key_url = f"{JIRA_BASE_URL}/browse/{key}"
        
        # 关键字列（A列）
        requests_body["requests"].append({
            "updateCell": {
                "cell": {
                    "hyperlink": {
                        "url": key_url
                    }
                },
                "range": {
                    "sheetId": SOURCE_SHEET_ID,
                    "rowIndex": row_idx,
                    "columnIndex": 0
                }
            }
        })
        
        # 概要列（B列）
        requests_body["requests"].append({
            "updateCell": {
                "cell": {
                    "hyperlink": {
                        "url": key_url
                    }
                },
                "range": {
                    "sheetId": SOURCE_SHEET_ID,
                    "rowIndex": row_idx,
                    "columnIndex": 1
                }
            }
        })
    
    # 发送批量更新请求
    batch_update_resp = requests.post(
        batch_update_url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json=requests_body,
        timeout=120
    )
    
    if batch_update_resp.status_code != 200:
        print(f"[INFO] 设置超链接失败：HTTP {batch_update_resp.status_code} {batch_update_resp.text}")
        print("[INFO] 继续执行后续步骤...")
    else:
        batch_update_data = batch_update_resp.json()
        if batch_update_data.get("code") != 0:
            print(f"[INFO] 设置超链接返回错误：code={batch_update_data.get('code')} msg={batch_update_data.get('msg')}")
            print("[INFO] 继续执行后续步骤...")
        else:
            print("[INFO] 成功设置超链接")
    
    # 无论是否有数据，都尝试获取表格信息（使用 v3 API）
    print("[INFO] 尝试获取表格信息...")
    sheet_info_url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{FEISHU_DOC_TOKEN}"
    sheet_info_resp = requests.get(sheet_info_url, headers={"Authorization": f"Bearer {feishu_token}"}, timeout=60)
    if sheet_info_resp.status_code == 200:
        sheet_info_data = sheet_info_resp.json()
        # print("[DEBUG] 表格信息响应：", sheet_info_data)
        if sheet_info_data.get("code") == 0:
            sheets = sheet_info_data["data"].get("sheets", [])
            print(f"[INFO] 文档共有 {len(sheets)} 个表格：")
            for sheet in sheets:
                print(f"[INFO] 表格ID: {sheet.get('sheetId')}, 名称: {sheet.get('title')}")
    else:
        print(f"[INFO] 获取表格信息失败：HTTP {sheet_info_resp.status_code} {sheet_info_resp.text}")

    # -------------------------- 3. 提取字段关键字、概要、修复版本到第二个文档 --------------------------
    print("[INFO] 正在提取字段到第二个文档...")
    # 提取需要的字段
    extracted_data = []
    # 假设表头在第一行，找到关键字、概要、修复版本的列索引
    if source_values:
        header = source_values[0]
        # 查找列索引
        key_column = -1
        summary_column = -1
        version_column = -1
        for i, col in enumerate(header):
            if "关键字" in col or "key" in col.lower() or "任务类型" in col:
                key_column = i
            elif "概要" in col or "summary" in col.lower() or "任务描述" in col:
                summary_column = i
            elif "修复版本" in col or "version" in col.lower() or "版本" in col:
                version_column = i
        
        print(f"[INFO] 列索引：关键字={key_column}, 概要={summary_column}, 修复版本={version_column}")
        
        if key_column == -1 or summary_column == -1 or version_column == -1:
            print("[ERROR] 无法找到关键字、概要、修复版本列")
            sys.exit(1)
        
        # 提取数据
        extracted_data.append(["关键字", "概要", "修复版本"])
        for row in source_values[1:]:
            if len(row) > max(key_column, summary_column, version_column):
                extracted_data.append([
                    row[key_column] if key_column < len(row) else "",
                    row[summary_column] if summary_column < len(row) else "",
                    row[version_column] if version_column < len(row) else ""
                ])
    
    print(f"[INFO] 提取了 {len(extracted_data) - 1} 条数据")
    
    # 检查提取的数据
    if not extracted_data:
        print("[ERROR] 没有提取到数据")
        sys.exit(1)
    
    # 清空并写入第二个文档
    extract_range = f"{EXTRACT_SHEET_ID}!A1:C{len(extracted_data)}"
    extract_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values"
    extract_resp = requests.put(
        extract_url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json={
            "valueRange": {
                "range": extract_range,
                "values": extracted_data
            }
        },
        timeout=60
    )
    if extract_resp.status_code != 200:
        print(f"[ERROR] 写入第二个文档失败：HTTP {extract_resp.status_code} {extract_resp.text}")
        sys.exit(1)
    print("[INFO] 成功写入第二个文档")

    # -------------------------- 4. 筛选剔除含有"日常资源版本"的记录 --------------------------
    print("[INFO] 正在筛选数据...")
    # 过滤数据
    filtered_data = [extracted_data[0]]  # 保留表头
    for row in extracted_data[1:]:
        version = row[2] if len(row) > 2 else ""
        if "日常资源版本" not in version:
            filtered_data.append(row)
    
    print(f"[INFO] 过滤后剩余 {len(filtered_data) - 1} 条数据")

    # -------------------------- 5. 按照修复版本字段进行归类排序 --------------------------
    print("[INFO] 正在排序数据...")
    # 按修复版本排序
    if len(filtered_data) > 1:
        # 提取数据行（排除表头）
        data_rows = filtered_data[1:]
        # 按修复版本排序
        data_rows.sort(key=lambda x: x[2] if len(x) > 2 else "")
        # 重新组合数据
        sorted_data = [filtered_data[0]] + data_rows
    else:
        sorted_data = filtered_data

    # -------------------------- 6. 输出到第三个文档 --------------------------
    print("[INFO] 正在写入第三个文档...")
    final_range = f"{FINAL_SHEET_ID}!A1:C{len(sorted_data)}"
    final_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values"
    final_resp = requests.put(
        final_url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json={
            "valueRange": {
                "range": final_range,
                "values": sorted_data
            }
        },
        timeout=60
    )
    if final_resp.status_code != 200:
        print(f"[ERROR] 写入第三个文档失败：HTTP {final_resp.status_code} {final_resp.text}")
        sys.exit(1)
    print("[INFO] 成功写入第三个文档")

    print("[INFO] 全部完成！")
    print(f"[INFO] 源表格：https://bytedance.larkoffice.com/sheets/{FEISHU_DOC_TOKEN}?sheet={SOURCE_SHEET_ID}")
    print(f"[INFO] 提取表格：https://bytedance.larkoffice.com/sheets/{FEISHU_DOC_TOKEN}?sheet={EXTRACT_SHEET_ID}")
    print(f"[INFO] 最终表格：https://bytedance.larkoffice.com/sheets/{FEISHU_DOC_TOKEN}?sheet={FINAL_SHEET_ID}")

except Exception as e:
    print(f"[ERROR] 发生未知错误：{str(e)}")
    print("[INFO] 错误堆栈：")
    print(traceback.format_exc())
