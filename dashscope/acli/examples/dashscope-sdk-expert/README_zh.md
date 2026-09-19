# DashScope SDK Expert —— 配置驱动的 acli 示例

> [English](README.md) | **中文** | [日本語](README_ja.md) | [Español](README_es.md) | [한국어](README_ko.md)

**在线文档**：https://help.aliyun.com/zh/model-studio/dashscope-sdk-expert

本示例演示如何利用 **AgenticCLI（acli）** 原生的配置机制，构建一个面向特定场景的 AI 专家 Agent。

**核心理念：配置驱动，零 Python 胶水代码。** Agent 的身份、能力、技能和知识索引全部由 `.acli/` 下的文件定义；下载示例后直接运行 `acli` 即可启动。

## 目录结构

```
dashscope-sdk-expert/
└── .acli/                      # Agent 配置目录
    ├── config.toml              # 模型与用户配置
    ├── custom-extensions.toml   # Provider 声明（tongyi）
    ├── hooks.toml               # 事件钩子
    ├── system-prompt.md         # System prompt（Agent 人设与行为规则）
    └── skills/                  # 技能模板（模型通过 use_skill 按需加载）
        ├── text-generation.md   # 文本生成（Generation / OpenAI 兼容，Python+Java）
        ├── multimodal.md        # 多模态（MultiModalConversation/ImageSynthesis/VideoSynthesis）
        ├── speech.md            # 语音（SpeechSynthesizer/Transcription）
        ├── retrieval.md         # 检索（Embedding/TextReRank/RAG）
        ├── fine-tuning.md       # 微调与部署（SFT/CPT/DPO/Deployments）
        ├── agent.md             # Agent（Application/Assistants/插件与 MCP）
        ├── cli.md               # dashscope CLI 命令参考
        ├── sdk-example.md       # 生成 SDK 代码示例
        ├── api-doc.md           # 查看 API 参数文档
        ├── diagnose.md          # 诊断 SDK 调用错误
        ├── error-code.md        # 解释错误码
        ├── explain-code.md      # 解释代码逻辑
        └── translate.md         # 中英文互译
```

## 快速开始

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# 将示例合并到 ./.acli/（同名文件会自动备份到 .acli/backup/；可用 example restore 撤销）
acli example download dashscope-sdk-expert

# 启动 —— 无需 cd，也无需 Python 启动脚本
acli
acli --tui
acli -c "How do I use Generation.call?"
```

## 配置驱动的实现方式

### 1. system-prompt.md —— Agent 人设

定义 Agent 的身份、知识范围和行为规则，是 Agent「是谁」的核心：

```markdown
You are DashScope SDK Expert, an intelligent assistant for the DashScope Python SDK...

## Grounded Knowledge First
Before answering, ALWAYS verify against the actual installed SDK...
```

### 2. skills/ —— 按需加载的领域知识库

SDK/CLI 的公开接口知识直接存放在各领域的 skill 中：每个领域一个文件，包含模型列表、Python 和 Java SDK 签名、输入输出结构以及错误码。回答 API 相关问题时，模型会通过 `use_skill` 按需加载匹配的 skill —— **不会有任何内容常驻在 system prompt 中** —— 首轮输入 token 因此减少约 16k 字符；skill 未覆盖的细节会回退到对已安装包执行 `inspect.signature` / `help()`。

### 3. skills/ —— 任务模板

每个 `.md` 文件都是一个带有 frontmatter 元数据的可复用 prompt 模板：

```yaml
---
name: sdk-example
description: Generate runnable DashScope SDK code examples
arguments: [api_name]
---

Before generating code, first verify the user's installed SDK version and API signature:
1. `run_command("python -c 'import dashscope; ...'")`
...
```

- **name**：skill 标识符，通过 `/skill` 命令调用
- **description**：简短描述；Agent 会据此判断何时应用该 skill
- **arguments**：模板变量，调用时会被替换为实际值

### 4. config.toml —— 运行时配置

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-dashscope"
```

## 复用这套模式

要为你自己的场景创建一个 AI 专家：

1. `acli example download dashscope-sdk-expert`（合并到你项目的 `./.acli/` 中）
2. 编辑 `.acli/system-prompt.md` —— 定义你的 Agent 人设
3. 编辑 `.acli/skills/` —— 添加你的领域知识和技能模板（模型按需加载）
4. 编辑 `.acli/config.toml` —— 选择合适的模型
5. 运行 `acli`

## 设计要点

| 传统方式 | acli 配置化方式 |
|---------|---------------|
| Prompt 硬编码在代码中 | `system-prompt.md` 文件 |
| 用 if-else 分支处理不同场景 | `skills/*.md` 模板库 |
| 把整份大文档塞进 prompt | `skills/` 领域知识按需加载 |
| 调整行为需要修改代码 | 只需编辑 Markdown |
| 难以共享和复用 | 整个 `.acli/` 目录都是可移植的 |
