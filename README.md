# Git AI Analyzer - 多仓库代码效率评估系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> 基于 AI 分析的多仓库代码效率评估系统，通过分析 Git 提交历史、代码质量和开发模式，为团队和个人提供全面的效率评估报告。

## 🌟 功能特性

### 📊 **智能效率评估**
- **多维度分析**：代码质量、生产力、协作、创新、维护等5个维度
- **AI 驱动**：使用 OpenAI/OpenRouter API 进行智能代码分析
- **综合评分**：基于多个指标的综合评分系统
- **绩效等级**：自动划分优秀、良好、一般、低于平均、较差等级

### 🔍 **深度代码分析**
- **代码质量评估**：AI 分析代码结构、可读性、最佳实践
- **复杂度分析**：评估代码复杂度和维护难度
- **工作量评估**：基于代码变更量和工作复杂度
- **技术栈识别**：自动识别 Java、JavaScript、C++、Go 等技术栈

### 📈 **生产力指标**
- **综合生产力计算**：考虑代码产出、提交效率、文件影响、复杂度权重
- **技术栈调整**：不同技术栈的生产力标准差异化
- **净代码产出**：新增代码减去删除代码的真实产出
- **提交效率**：避免频繁小提交的优化建议

### 🏢 **团队管理功能**
- **多仓库支持**：同时分析多个 Git 仓库
- **员工映射**：支持多邮箱映射，准确识别员工贡献
- **团队统计**：团队整体表现和分布分析
- **个性化报告**：针对个人和团队的详细报告

### 📋 **报告生成**
- **多种格式**：JSON、HTML、PDF 格式报告
- **可视化图表**：绩效分布、仓库活跃度、员工评分等图表
- **关键发现**：自动生成关键发现和改进建议
- **详细分析**：包含代码质量、生产力、协作等详细指标

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Git
- OpenAI API Key 或 OpenRouter API Key

### 安装步骤

1. **克隆仓库**
```bash
git clone <repository-url>
cd git_ai_analyzer
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，添加你的 API Key
OPENAI_API_KEY=your_openai_api_key_here
# 或使用 OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

5. **配置仓库和员工**
编辑 `config.yaml` 文件，配置要分析的仓库和员工映射。

## 📖 使用指南

### 基本用法

```bash
# 月度评估（默认）
python main.py --period monthly

# 周度评估
python main.py --period weekly

# 自定义天数评估
python main.py --custom-days 14

# 指定输出目录
python main.py --period monthly --output-dir results

# 调试模式
python main.py --period monthly --log-level DEBUG
```

### 生成 PDF 报告

```bash
# 运行评估后生成 PDF 报告
python generate_pdf_report.py
```

### 配置说明

#### 仓库配置
```yaml
repositories:
  - name: "project-name"
    path: "./path/to/repo"
    weight: 1.0
    description: "项目描述"
```

#### 员工映射配置
```yaml
employee_mapping:
  "员工姓名": ["email1@example.com", "email2@example.com"]
  "张三": ["zhangsan@company.com", "zhangsan@gmail.com"]
```

#### 评估指标权重
```yaml
metrics:
  code_quality: 0.3      # 代码质量权重
  productivity: 0.25     # 生产力权重
  collaboration: 0.2     # 协作权重
  innovation: 0.15       # 创新权重
  maintenance: 0.1       # 维护权重
```

## 📊 评估指标详解

### 代码质量 (30%)
- **AI 分析评分**：基于代码结构、可读性、最佳实践
- **Bug 修复比例**：bugfix 类型提交占比
- **代码复杂度**：AI 评估的代码复杂度等级

### 生产力 (25%)
- **综合生产力**：代码产出 × 复杂度权重 × 技术栈权重
- **提交效率**：合理的提交频率和规模
- **文件影响**：变更文件数量和影响范围

### 协作 (20%)
- **Bug 修复贡献**：修复问题的贡献度
- **代码审查参与**：参与代码审查的频率
- **合并冲突处理**：解决合并冲突的能力

### 创新 (15%)
- **新功能贡献**：feature 类型提交数量
- **技术创新**：引入新技术或架构改进
- **技术债务减少**：重构和技术改进

### 维护 (10%)
- **维护性提交**：refactor、bugfix 等维护工作
- **文档质量**：文档更新和维护
- **测试覆盖**：测试代码的贡献

## 🏗️ 项目结构

```
git_ai_analyzer/
├── main.py                 # 主程序入口
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖文件
├── generate_pdf_report.py # PDF报告生成器
├── .gitignore            # Git忽略文件
├── README.md             # 项目文档
├── src/                  # 源代码目录
│   ├── __init__.py
│   ├── config.py         # 配置管理
│   ├── models.py         # 数据模型
│   ├── git_analyzer.py   # Git分析器
│   ├── ai_analyzer.py    # AI分析器
│   └── efficiency_engine.py # 效率评估引擎
├── analysis_results/     # 分析结果目录
│   ├── data/            # 评估数据
│   ├── reports/         # 生成报告
│   ├── charts/          # 图表文件
│   ├── cache/           # AI分析缓存
│   └── logs/            # 日志文件
└── venv/                # 虚拟环境
```

## 🔧 配置选项

### OpenAI/OpenRouter 配置
```yaml
openai:
  model: "gpt-4"
  max_retries: 6
  base_delay: 2.0
  request_interval: 3.0

openrouter:
  enabled: false
  model: "openai/gpt-4.1-mini"
  base_url: "https://openrouter.ai/api/v1"
```

### Git 配置
```yaml
git:
  max_commits: 1000
  since_days: 30
  exclude_merge_commits: true
  exclude_empty_commits: true
```

### 输出配置
```yaml
output:
  base_dir: "analysis_results"
  formats: ["json", "html", "pdf"]
  charts: true
  reports: true
```

## 📈 示例报告

### 团队总体评分
```
团队总体评分：0.47/1.0

绩效分布：
- 优秀：0 人
- 良好：0 人  
- 一般：3 人
- 低于平均：3 人
- 较差：2 人
```

### 员工详细指标
```
员工：张三
- 综合评分：0.69
- 代码质量：0.83
- 生产力：1.17提交/天
- 净代码产出：2462行
- 新功能贡献：11个
- 维护提交：14个
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 开发计划

- [ ] 支持更多代码质量分析工具集成
- [ ] 添加实时监控和告警功能
- [ ] 开发 Web 管理界面
- [ ] 支持更多 Git 托管平台
- [ ] 添加团队协作分析功能
- [ ] 支持自定义评估模型

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的 AI 分析能力
- [OpenRouter](https://openrouter.ai/) - 提供 API 代理服务
- [GitPython](https://gitpython.readthedocs.io/) - Git 操作库
- [ReportLab](https://www.reportlab.com/) - PDF 生成库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue：[GitHub Issues](https://github.com/goplus-labs/codeAnalysis.git)
- 邮箱：allen@gopluslabs.io

---

**注意**：本项目需要 OpenAI API Key 或 OpenRouter API Key 才能正常运行。请确保您有足够的 API 配额。 