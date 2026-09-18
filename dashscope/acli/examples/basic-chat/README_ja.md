# Basic Chat — 最小構成で動く acli の例

> [English](README.md) | [中文](README_zh.md) | **日本語**

最小限の設定で、Web 検索機能を備えた汎用チャットエージェントを起動する方法を示します。**すべての知能は `.acli/` の設定に存在しており、Python の起動コードは一切ありません**——`acli` をダウンロードしてそのまま実行するだけです。

## ディレクトリ構成

```
basic-chat/
└── .acli/
    ├── config.toml                   # デフォルトの provider/model/user_name
    ├── custom-extensions.toml        # tongyi provider の宣言 + capability/skill/shell_tool のコメントテンプレート
    ├── hooks.toml                    # イベントフック（before/after_tool_call、on_error など）のコメントテンプレート
    ├── system-prompt.md              # エージェントのペルソナと行動ルール
    └── skills/
        ├── research-topic.md         # トピックを Web 検索してブリーフィングを作成（web_search を呼び出す）
        ├── explain-code.md           # コードのロジックを説明
        ├── translate.md              # 中国語⇔英語の翻訳
        └── write-poem.md             # 七言絶句を作る（純粋な prompt テンプレートのデモ）
```

## クイックスタート

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# サンプルを ./.acli/ にマージする（同名ファイルは自動的に .acli/backup/ にバックアップされ、example restore で元に戻せます）
acli example download basic-chat

# 必要な provider を .acli/custom-extensions.toml に追加する
# .acli/system-prompt.md を編集してエージェントのペルソナを定義する
# .acli/skills/ に独自の skill テンプレートを追加する

# 起動（cd は不要、設定はすでにカレントディレクトリにあります）
acli
acli --tui
acli -c "hello"
```

> 新しいディレクトリで使いたい場合は？ `mkdir my-agent && cd my-agent && acli example download basic-chat` を実行するか、
> `acli example download basic-chat --target my-agent` を使ってください。

## プログラムとしての設定

### custom-extensions.toml —— Provider の宣言

acli が利用できる LLM provider を宣言します。最小構成では `[[providers]]` ブロックが1つあれば十分です：

```toml
[[providers]]
name = "tongyi"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key_env = "DASHSCOPE_API_KEY"      # ← 環境変数名のみを保存し、sk-xxx はシェルから提供されます
default_model = "qwen3.8-max"
models = ["qwen3.8-max", "qwen3.7-max", "qwen3.7-plus", "qwen-turbo", "qwen-vl-max"]
vision_models = ["qwen-vl-max"]        # ← これらのモデルが画像入力を受け付けることを acli に伝えます
protocol = "openai"                     # ← openai / anthropic / dashscope
```

Claude / GPT / ローカルの Ollama を使いたい場合は、toml 内の対応する `[[providers]]` ブロックのコメントを外すだけです。

**API Key を指定する3つの方法**（推奨度が高い順）：

1. `api_key_env = "FOO_API_KEY"` —— シェルで `export FOO_API_KEY=sk-xxx` を実行する方法。toml を git にコミットしても安全です
2. `/provider` ウィザードによる対話的な入力 —— `api_key = "ENC:..."`（端末に紐づく暗号化）が書き込まれます
3. 平文の `api_key = "sk-xxx"` —— ローダーによって拒否されます。あくまでプレースホルダーの例示です

### system-prompt.md —— エージェントのペルソナ

エージェントが「何者であるか」を定義します。acli は起動時に `.acli/system-prompt.md` を自動的に読み込みます（ワークスペース側の設定が `~/.acli/system-prompt.md` より優先されます）。

### skills/*.md —— Prompt テンプレート

各 `.md` ファイルは、YAML フロントマターを持つ再利用可能な prompt です：

```yaml
---
name: research-topic
description: Web-search a topic and produce a briefing with source URLs
arguments: [topic]
---

Use the web_search tool to research "{topic}":
...
```

呼び出し方法：
- `/skill research-topic quantum computing` —— 明示的な呼び出し
- 自然言語："help me research the latest progress in quantum computing" —— LLM が使用するかどうかを判断します

`research-topic` は、prompt を使って LLM に組み込みの `web_search` ツールを呼び出させ、オンラインで情報収集を行わせる方法を示しています。

### config.toml —— デフォルト設定

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-basic"
```

## 次のステップ

- **provider を追加する**：`custom-extensions.toml` に `[[providers]]` ブロックを追加します
- **HTTP ツールを追加する**：`[[capabilities]]` + `[[capabilities.tools]]` ブロックを追加します（画像生成やリモートのワークフローエンジン呼び出しなど）
- **ビジョン機能を追加する**：`type = "vision"` の capability ツールを追加し、テキストエージェントが必要に応じてビジョン LLM を呼び出せるようにします
- **shell ツールを追加する**：`[[shell_tools]]` ブロックを追加して、よく使うローカルコマンドをラップします
- **フックを追加する**：`.acli/hooks.toml` でツール呼び出し前後のフックを設定します（例：`.py` ファイル書き込み後に自動で `py_compile` を実行する、`pip install` の前に確認を求める、ファイル削除をブロックするなど）。`.acli/hooks.toml` のテンプレートを参照してください。5つのイベント（`before_tool_call` / `after_tool_call` / `on_error` / `on_message` / `on_response`）× 6つのアクション（run/block/confirm/warn/alert/log）をすべてカバーしています。
- **永続的な知識を追加する**：system prompt に**常に**表示させたいドキュメント（API インデックスなど）を `.acli/references/*.md` に配置します
- **ペルソナを変更する**：`system-prompt.md` を編集します——例えば「コードレビュアー」「データアナリスト」「カスタマーサポート担当」に作り変えることができます

完全な機能ドキュメントについては、プロジェクトルートの `README.md` を参照してください。
