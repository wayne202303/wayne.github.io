# OpenClaw 完整使用指南

> 王楠的 OpenClaw 快速上手手册

---

## 📋 目录

1. [快速开始](#快速开始)
2. [常用命令](#常用命令)
3. [飞书集成](#飞书集成)
4. [记忆系统](#记忆系统)
5. [安全配置](#安全配置)

---

## 🚀 快速开始

### 检查状态

```bash
openclaw status
```

### 查看日志

```bash
openclaw logs --follow
```

### 更新 OpenClaw

```bash
openclaw update
```

---

## 💻 常用命令

### 状态管理

| 命令 | 说明 |
|------|------|
| `openclaw status` | 查看完整状态 |
| `openclaw status --all` | 查看所有状态 |
| `openclaw gateway probe` | 检查 Gateway 连接 |
| `openclaw security audit` | 安全审计 |
| `openclaw security audit --deep` | 深度安全审计 |

### 日志管理

| 命令 | 说明 |
|------|------|
| `openclaw logs` | 查看日志 |
| `openclaw logs --follow` | 实时跟踪日志 |

---

## 📱 飞书集成

### 已启用的飞书插件

你的 OpenClaw 已经配置了以下飞书插件：

- ✅ **feishu_doc** - 飞书文档（创建、编辑、读取）
- ✅ **feishu_chat** - 飞书聊天（发送消息、查看聊天记录）
- ✅ **feishu_wiki** - 飞书知识库（浏览、搜索文档）
- ✅ **feishu_drive** - 飞书云空间（文件管理）
- ✅ **feishu_bitable** - 飞书多维表格（数据管理）

### 飞书使用示例

#### 1. 查看日历

```bash
lark-cli calendar +agenda
```

#### 2. 查看聊天记录

```bash
# 查看指定群聊消息
lark-cli im +messages-list --chat-id <chat-id> --limit 50

# 搜索消息
lark-cli im +messages-search --query "关键词"
```

#### 3. 创建文档

```bash
# 创建飞书文档
lark-cli doc +create --title "文档标题" --content "文档内容"
```

#### 4. 查看知识库

```bash
# 列出知识库
lark-cli wiki +spaces

# 搜索文档
lark-cli wiki +search --query "搜索词"
```

---

## 🧠 记忆系统

### OpenClaw 内置记忆

OpenClaw 有自己的记忆系统，但你也可以配合我们刚搭建的 **5 层记忆架构**使用：

| 记忆类型 | 位置 | 说明 |
|---------|------|------|
| **OpenClaw Memory** | `~\.openclaw\memory\` | OpenClaw 内置记忆 |
| **MEMORY.md** | 项目根目录 | 长期记忆（精炼事实） |
| **SESSION-STATE.md** | 项目根目录 | 恢复层（当前任务） |
| **working-buffer.md** | 项目根目录 | 毛坯层（临时决策） |
| **memory-capture.md** | 项目根目录 | 记忆捕获模板 |
| **memory/YYYY-MM-DD.md** | memory/ 目录 | 每日笔记 |

### 使用 OpenClaw memory_search

```bash
# 在对话中使用
memory_search(query="相关关键词")
```

---

## 🔒 安全配置

### 当前安全状态

根据 `openclaw status`，有以下安全警告需要注意：

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 **CRITICAL** | 4 | 严重警告 |
| 🟡 **WARN** | 4 | 警告 |
| 🟢 **INFO** | 1 | 信息 |

### 建议的安全改进

#### 1. 小模型沙箱化

如果使用小模型（≤300B 参数），建议：

```toml
# 在 OpenClaw 配置中添加
[agents.defaults.sandbox]
mode = "all"

[tools.deny]
deny = ["group:web", "browser"]
```

#### 2. Feishu Group Policy

建议将 groupPolicy 改为 "allowlist"：

```toml
[channels.feishu]
groupPolicy = "allowlist"
groupAllowlist = ["你的群聊ID列表"]
```

#### 3. 限制文件系统工具

```toml
[tools.fs]
workspaceOnly = true
```

---

## 📊 当前 OpenClaw 状态

### 概览

| 项目 | 值 |
|------|-----|
| **Dashboard** | http://127.0.0.1:18789/ |
| **OS** | Windows 10.0.26100 (x64) |
| **Node** | 24.14.0 |
| **Agents** | 1 个 |
| **Sessions** | 2 个 active |

### 会话信息

| 会话 | 模型 | Token 使用 |
|------|------|-----------|
| agent:main:main | qwen3-vl:30b | 14k/262k (5%) |
| agent:main:feishu:direct:... | ep-20260309185921-llrrt | 未知/16k |

---

## 🎯 下一步建议

1. **启动 Gateway** - 如果需要使用 Dashboard
2. **配置安全** - 修复安全警告
3. **使用记忆** - 结合 5 层记忆架构
4. **探索飞书** - 充分利用已配置的飞书插件

---

## 🔗 相关链接

- OpenClaw 文档: https://docs.openclaw.ai
- FAQ: https://docs.openclaw.ai/faq
- 故障排除: https://docs.openclaw.ai/troubleshooting
