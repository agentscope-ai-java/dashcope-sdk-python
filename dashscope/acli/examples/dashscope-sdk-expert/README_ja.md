# DashScope SDK Expert —— 設定駆動型の acli の例

> [English](README.md) | [中文](README_zh.md) | **日本語** | [Español](README_es.md) | [한국어](README_ko.md)

**オンラインガイド**：https://help.aliyun.com/en/model-studio/dashscope-sdk-expert

この例は、**AgenticCLI（acli）** のネイティブな設定機構を使って、特定のシナリオに特化した AI エキスパートエージェントを構築する方法を示しています。

**基本コンセプト：設定駆動、Python によるグルーコードは不要。** エージェントのアイデンティティ、能力、スキル、ナレッジインデックスはすべて `.acli/` 配下のファイルで定義されます。サンプルをダウンロードして `acli` を実行するだけで起動できます。

## ディレクトリ構成

```
dashscope-sdk-expert/
└── .acli/                      # エージェント設定ディレクトリ
    ├── config.toml              # モデルとユーザーの設定
    ├── custom-extensions.toml   # Provider の宣言（tongyi）
    ├── hooks.toml               # イベントフック
    ├── system-prompt.md         # System prompt（エージェントのペルソナと行動ルール）
    └── skills/                  # スキルテンプレート（use_skill によりモデルが必要に応じて読み込む）
        ├── text-generation.md   # テキスト生成（Generation / OpenAI 互換、Python+Java）
        ├── multimodal.md        # マルチモーダル（MultiModalConversation/ImageSynthesis/VideoSynthesis）
        ├── speech.md            # 音声（SpeechSynthesizer/Transcription）
        ├── retrieval.md         # 検索（Embedding/TextReRank/RAG）
        ├── fine-tuning.md       # ファインチューニングとデプロイ（SFT/CPT/DPO/Deployments）
        ├── agent.md             # エージェント（Application/Assistants/プラグインと MCP）
        ├── cli.md               # dashscope CLI コマンドリファレンス
        ├── sdk-example.md       # SDK コード例を生成
        ├── api-doc.md           # API パラメータのドキュメントを参照
        ├── diagnose.md          # SDK 呼び出しエラーを診断
        ├── error-code.md        # エラーコードの説明
        ├── explain-code.md      # コードのロジックを説明
        └── translate.md         # 中国語⇔英語の翻訳
```

## クイックスタート

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# サンプルを ./.acli/ にマージする（同名ファイルは自動的に .acli/backup/ にバックアップされ、example restore で元に戻せます）
acli example download dashscope-sdk-expert

# 起動 —— cd も Python の起動スクリプトも不要です
acli
acli --tui
acli -c "How do I use Generation.call?"
```

## 設定駆動アプローチの仕組み

### 1. system-prompt.md —— エージェントのペルソナ

エージェントのアイデンティティ、知識範囲、行動ルールを定義します。これはエージェントが「何者であるか」の核心部分です：

```markdown
You are DashScope SDK Expert, an intelligent assistant for the DashScope Python SDK...

## Grounded Knowledge First
Before answering, ALWAYS verify against the actual installed SDK...
```

### 2. skills/ —— 必要に応じて読み込まれるドメイン知識ベース

SDK/CLI の公開インターフェースに関する知識は、ドメインごとの skill に直接格納されています：ドメインごとに1ファイルで、モデル一覧、Python と Java の SDK シグネチャ、入出力構造、エラーコードが含まれます。API に関する質問に答える際、モデルは `use_skill` によって該当する skill を必要に応じて読み込みます——**system prompt に常駐する内容は一切ありません**——これにより最初のターンの入力トークンが約16,000文字削減されます。skill でカバーされていない詳細は、インストール済みパッケージに対する `inspect.signature` / `help()` にフォールバックします。

### 3. skills/ —— タスクテンプレート

各 `.md` ファイルは、フロントマターのメタデータを持つ再利用可能な prompt テンプレートです：

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

- **name**：skill の識別子。`/skill` コマンドで呼び出します
- **description**：短い説明。エージェントはこれを見て、いつこの skill を適用するかを判断します
- **arguments**：テンプレート変数。呼び出し時に実際の値に置き換えられます

### 4. config.toml —— 実行時設定

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-dashscope"
```

## このパターンを再利用する

自分のシナリオ向けに AI エキスパートを作成するには：

1. `acli example download dashscope-sdk-expert`（プロジェクトの `./.acli/` にマージされます）
2. `.acli/system-prompt.md` を編集 —— 自分のエージェントのペルソナを定義します
3. `.acli/skills/` を編集 —— 自分のドメイン知識とスキルテンプレートを追加します（モデルが必要に応じて読み込みます）
4. `.acli/config.toml` を編集 —— 適切なモデルを選択します
5. `acli` を実行します

## 設計上のポイント

| 従来のアプローチ | acli の設定駆動アプローチ |
|---------|---------------|
| コードにハードコードされた prompt | `system-prompt.md` ファイル |
| シナリオごとの if-else 分岐 | `skills/*.md` テンプレートライブラリ |
| 巨大なドキュメントをすべて prompt に詰め込む | `skills/` のドメイン知識を必要に応じて読み込み |
| 動作を変えるにはコード修正が必要 | Markdown を編集するだけ |
| 共有・再利用が困難 | `.acli/` ディレクトリ全体が可搬 |
