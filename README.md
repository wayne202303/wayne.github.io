# 手游配表检查工具

一个用于对比手游策划表差异的命令行工具，支持Excel和CSV格式，专为CI/CD流程设计。

## 功能特性

- 📊 支持Excel(.xlsx, .xls)和CSV格式的配表
- 🔍 检测工作表的新增、删除和修改
- 📋 检测列的新增和删除
- 📝 检测行的新增、删除和修改
- 🔑 支持主键对比，更准确地识别记录变更
- 🚫 支持忽略指定的列和工作表
- 📄 支持生成JSON和HTML格式的差异报告
- 💻 命令行界面，易于集成到CI/CD工作流中
- 🎯 支持配置文件管理
- ⚡ 发现差异时返回非零退出码，便于CI/CD判断

## 安装

### 方式一：从源码安装（推荐）

```bash
git clone <repository-url>
cd NewProject
pip install -e .
```

### 方式二：使用pip安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

对比两个配表文件：

```bash
config-diff sample_old.xlsx sample_new.xlsx
```

### 生成报告

```bash
config-diff sample_old.xlsx sample_new.xlsx --html report.html --json report.json
```

### 使用主键对比

```bash
config-diff sample_old.xlsx sample_new.xlsx --primary-key Hero:id --primary-key Item:id
```

### 忽略指定列和工作表

```bash
config-diff sample_old.xlsx sample_new.xlsx --ignore-column remark --ignore-sheet Log
```

### 使用配置文件

```bash
config-diff sample_old.xlsx sample_new.xlsx --config config-example.yaml
```

### CI/CD模式

发现差异时返回非零退出码：

```bash
config-diff sample_old.xlsx sample_new.xlsx --fail-on-diff --quiet
```

### 显示详细信息

```bash
config-diff sample_old.xlsx sample_new.xlsx --verbose
```

## 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `old_file` | - | 旧配表文件路径（必需） |
| `new_file` | - | 新配表文件路径（必需） |
| `--config` | `-c` | 配置文件路径（YAML格式） |
| `--json` | - | 输出JSON报告路径 |
| `--html` | - | 输出HTML报告路径 |
| `--primary-key` | `-k` | 指定主键，格式: `sheet_name:column_name`（可多次使用） |
| `--ignore-column` | `-i` | 指定忽略的列名（可多次使用） |
| `--ignore-sheet` | `-s` | 指定忽略的工作表名（可多次使用） |
| `--verbose` | `-v` | 显示详细信息 |
| `--quiet` | `-q` | 静默模式，不输出到控制台 |
| `--fail-on-diff` | `-f` | 发现差异时返回非零退出码 |
| `--version` | `-V` | 显示版本信息 |

## 配置文件

创建 `config-diff.yaml` 文件：

```yaml
primary_keys:
  Hero: id
  Item: id
  Skill: id

ignore_columns:
  - create_time
  - update_time
  - remark

ignore_sheets:
  - Log
  - Temp

output_dir: ./reports
```

然后使用：

```bash
config-diff old.xlsx new.xlsx --config config-diff.yaml
```

## CI/CD 集成

### GitHub Actions

在 `.github/workflows/config-diff.yml` 中添加：

```yaml
name: Config Diff Check
on:
  pull_request:
    paths:
      - '**.xlsx'
      - '**.xls'
      - '**.csv'

jobs:
  config-diff:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install config-diff
      run: pip install .
    
    - name: Run diff check
      run: |
        config-diff old_config.xlsx new_config.xlsx \
          --html diff_report.html \
          --json diff_report.json \
          --fail-on-diff
```

### GitLab CI

在 `.gitlab-ci.yml` 中添加：

```yaml
config_diff:
  stage: test
  image: python:3.11
  script:
    - pip install .
    - config-diff old_config.xlsx new_config.xlsx --fail-on-diff
  only:
    changes:
      - "*.xlsx"
      - "*.xls"
      - "*.csv"
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无差异或成功执行 |
| 1 | 发现差异（使用 `--fail-on-diff` 时） |
| 2 | 执行错误 |

## 输出报告

### HTML报告
- 可视化展示所有差异
- 颜色标记：绿色（新增）、红色（删除）、橙色（修改）
- 可在浏览器中直接查看

### JSON报告
- 结构化的差异数据
- 便于程序解析和进一步处理

## 项目结构

```
.
├── src/
│   └── config_diff_tool/
│       ├── __init__.py      # 版本信息
│       ├── cli.py           # 命令行入口
│       ├── reader.py        # 配表读取模块
│       ├── differ.py        # 差异比较核心逻辑
│       ├── reporter.py      # 报告生成模块
│       └── config.py        # 配置文件处理
├── .github/
│   └── workflows/
│       └── config-diff.yml  # GitHub Actions示例
├── config-example.yaml      # 配置文件示例
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── generate_samples.py     # 生成示例数据
├── README.md              # 说明文档
└── sample_old.xlsx        # 示例旧配表
└── sample_new.xlsx        # 示例新配表
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/
```

## 许可证

MIT License
