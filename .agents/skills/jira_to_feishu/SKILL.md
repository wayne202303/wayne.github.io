# Jira to Feishu Skill

## 技能信息
- **名称**: jira_to_feishu
- **版本**: 1.0.0
- **描述**: 从 Jira 拉取测试中状态的任务并写入飞书表格
- **作者**: Trae AI
- **依赖**: requests, python-dotenv, python-dateutil

## 功能说明
- 从 Jira 拉取 MK 项目中"测试中"状态的任务
- 过滤掉"日常资源版本"和包含"loc"的任务
- 按版本和更新时间排序
- 自动追加写入飞书多维表格
- 支持错误处理和详细日志输出

## 配置要求
1. **环境变量**:
   - JIRA_BASE_URL: Jira 实例地址
   - JIRA_TOKEN: Jira API 令牌

2. **飞书配置** (在脚本中硬编码):
   - FEISHU_APP_ID: 飞书应用ID
   - FEISHU_APP_SECRET: 飞书应用密钥
   - FEISHU_DOC_TOKEN: 飞书文档令牌
   - FEISHU_SHEET_ID: 飞书表格ID

## 使用方法
1. 安装依赖: `pip install -r requirements.txt`
2. 配置环境变量
3. 运行: `python scripts/jira_to_feishu.py`

## 输出
- 控制台日志
- 飞书表格数据

## 错误处理
- 配置错误: 提示缺少必要配置
- API 错误: 显示详细错误信息
- 编码错误: 已处理 Windows 命令行编码问题
