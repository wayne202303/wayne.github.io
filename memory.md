# MEMORY.md

> 长期记忆。只保留会持续影响协作的事实、偏好和决策。

## User

- Preferred name: 王楠
- Timezone: Asia/Shanghai
- Preferred language: 中文
- Tools: 飞书 CLI, Sensight, 虾评Skill
- Environment: Windows + PowerShell

## 当前任务

- [ ] 正在搭建 Agent 记忆系统
- [x] 已下载 memory-system 技能
- [x] 已完成虾评Skill账号注册

## 决策记录

- 2026-04-13: 决定采用 memory-system 技能的 5 层记忆架构
- 2026-04-13: 注册虾评Skill平台，用户名为 trae-user
- 2026-04-10: 安装了 Sensight 技能用于获取 AI 新闻
- 2026-04-10: 配置了飞书 CLI 认证，可以访问飞书日历、文档等

## 踩坑记录

- MCP 服务器启动失败问题 → 解决方法：需要在配置中添加 registry 参数指向 http://bnpm.byted.org/
- 飞书发送消息需要权限 → 解决方法：需要先获取 im:message.send_as_user 权限
- 虾评Skill注册需要数学挑战题 → 解决方法：去除噪声符号后计算数学题答案

## 项目约定

- 记忆文件统一使用 UTF-8 编码
- 每日笔记命名格式：YYYY-MM-DD.md
- 重要决策必须记录日期和原因
- MEMORY.md 保持精炼，不超过 200 行
