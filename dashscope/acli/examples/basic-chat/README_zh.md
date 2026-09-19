# Basic Chat — 最小可用的 acli 示例

> [English](README.md) | **中文** | [日本語](README_ja.md) | [Español](README_es.md) | [한국어](README_ko.md)

演示如何用最少的配置启动一个具备联网搜索能力的通用聊天 Agent。**所有的智能都体现在 `.acli/` 配置中——没有任何 Python 启动代码**——直接下载并运行 `acli` 即可。

## 目录结构

```
basic-chat/
└── .acli/
    ├── config.toml                   # 默认的 provider/model/user_name
    ├── custom-extensions.toml        # tongyi provider 声明 + capability/skill/shell_tool 注释模板
    ├── hooks.toml                    # 事件钩子（before/after_tool_call、on_error 等）注释模板
    ├── system-prompt.md              # Agent 人设与行为规则
    └── skills/
        ├── research-topic.md         # 对某个主题进行联网搜索并生成简报（调用 web_search）
        ├── explain-code.md           # 解释代码逻辑
        ├── translate.md              # 中英文互译
        └── write-poem.md             # 写一首七言绝句（演示纯 prompt 模板的用法）
```

## 快速开始

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# 将示例合并到 ./.acli/（同名文件会自动备份到 .acli/backup/；可用 example restore 撤销）
acli example download basic-chat

# 编辑 .acli/custom-extensions.toml 添加你需要的 provider
# 编辑 .acli/system-prompt.md 定义 Agent 人设
# 在 .acli/skills/ 下添加你自己的 skill 模板

# 启动（无需 cd，配置已在当前目录下）
acli
acli --tui
acli -c "hello"
```

> 想在全新目录中使用？执行 `mkdir my-agent && cd my-agent && acli example download basic-chat`，
> 或者使用 `acli example download basic-chat --target my-agent`。

## 配置即程序

### custom-extensions.toml —— Provider 声明

声明 acli 可以使用哪些 LLM provider。最简配置只需要一个 `[[providers]]` 块：

```toml
[[providers]]
name = "tongyi"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key_env = "DASHSCOPE_API_KEY"      # ← 只存储环境变量名；sk-xxx 由 shell 提供
default_model = "qwen3.8-max"
models = ["qwen3.8-max", "qwen3.7-max", "qwen3.7-plus", "qwen-turbo", "qwen-vl-max"]
vision_models = ["qwen-vl-max"]        # ← 告诉 acli 这些模型支持图片输入
protocol = "openai"                     # ← openai / anthropic / dashscope
```

想用 Claude / GPT / 本地 Ollama？只需取消 toml 中对应 `[[providers]]` 块的注释即可。

**提供 API Key 的三种方式**（按推荐程度递减排序）：

1. `api_key_env = "FOO_API_KEY"` —— 在 shell 中 `export FOO_API_KEY=sk-xxx`；toml 可以安全地提交到 git
2. `/provider` 交互式向导 —— 写入 `api_key = "ENC:..."`（与本机绑定的加密存储）
3. 明文 `api_key = "sk-xxx"` —— 会被加载器拒绝；仅作占位示例

### system-prompt.md —— Agent 人设

定义 Agent「是谁」。acli 启动时会自动加载 `.acli/system-prompt.md`（工作目录下的配置优先于 `~/.acli/system-prompt.md`）。

### skills/*.md —— Prompt 模板

每个 `.md` 文件都是一个带 YAML frontmatter 的可复用 prompt：

```yaml
---
name: research-topic
description: Web-search a topic and produce a briefing with source URLs
arguments: [topic]
---

Use the web_search tool to research "{topic}":
...
```

调用方式：
- `/skill research-topic quantum computing` —— 显式调用
- 自然语言："help me research the latest progress in quantum computing" —— 由 LLM 自行判断是否使用该 skill

`research-topic` 演示了如何用 prompt 引导 LLM 调用内置的 `web_search` 工具来进行联网信息收集。

### config.toml —— 默认配置

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-basic"
```

## 下一步

- **添加更多 provider**：在 `custom-extensions.toml` 中添加 `[[providers]]` 块
- **添加 HTTP 工具**：添加 `[[capabilities]]` + `[[capabilities.tools]]` 块（例如图像生成、调用远程工作流引擎）
- **添加视觉能力**：添加一个 `type = "vision"` 的 capability 工具，让文本 Agent 可以按需调用视觉 LLM
- **添加 shell 工具**：添加 `[[shell_tools]]` 块来封装常用的本地命令
- **添加钩子**：在 `.acli/hooks.toml` 中配置工具调用前/后的钩子（例如写入 `.py` 文件后自动 `py_compile`、`pip install` 前需要确认、阻止文件删除）。参见 `.acli/hooks.toml` 中的模板，覆盖全部 5 种事件（`before_tool_call` / `after_tool_call` / `on_error` / `on_message` / `on_response`）× 6 种动作（run/block/confirm/warn/alert/log）。
- **添加持久化知识**：把必须**始终**出现在 system prompt 中的文档（例如某个 API 索引）放到 `.acli/references/*.md`
- **更换人设**：编辑 `system-prompt.md`——例如把它改造成「代码审查员」「数据分析师」或「客服坐席」

完整功能文档请参见项目根目录的 `README.md`。
