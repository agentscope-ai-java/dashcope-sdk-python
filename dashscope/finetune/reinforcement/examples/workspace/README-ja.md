# Agentic RL SDK/CLI 使用ガイド [[English]](./README.md) [[中文]](./README-zh.md) [[Español]](./README-es.md) [[한국어]](./README-ko.md)

## 1. SDK のインストール

```bash
pip install dashscope>=1.25.19
```

## 2. 環境設定

### 2.1 環境変数の設定

```bash
# 必須：API キー（コード内で初期化することも可能: AgenticRL(api_key="for your api key") ）
export DASHSCOPE_API_KEY="your_api_key_here"

# 任意：ログレベル設定 info/debug/warning/critical（デフォルト info）
export LOG_LEVEL="info"
```

### 2.2 依存関係ファイルの設定

> 注：`requirements.txt` はリモートの Function Compute 環境（Python >= 3.10）で使用されます。ローカルデバッグの際は Python 3.10 以上を使用してください。`dashscope` SDK 自体は Python 3.8 以上に対応しています。

以下のコア依存関係を含む `requirements.txt` ファイルを作成します：

```requirements.txt
# 基本（必須）
dashscope>=1.25.19

# フレームワーク依存関係
fastapi==0.136.0
uvicorn==0.45.0
# 省略

# 軌跡（トラジェクトリ）関数の依存関係
langchain-core==1.3.0
langchain-mcp-adapters==0.2.2
langchain-openai==1.2.0
# 省略

# その他のカスタム依存関係を追加...
```

## 3. 関数開発とデータ準備

### 3.1 関数コンポーネントの作成

`functions` ディレクトリ以下に関数を実装します：

- **Reward 関数テンプレート**：
    - `functions/reward/reward.py` - 基本実装
    - `functions/reward/reward_decorator.py` - デコレーター実装
- **Rollout 関数テンプレート**：
    - `functions/rollout/rollout.py` - 基本実装

> 注：`functions/` ディレクトリには `__init__.py` ファイルが必要です

関数コンポーネントが必要かどうかは、選択したトレーニング設定によって異なります：

| 設定 | モード | カスタム Rollout | カスタム Reward |
|---|---|---:|---:|
| `rl-job.yaml` | 通常の強化学習 | 必須 | 少なくとも1つ |
| `opd-job.yaml`（関数ブロックなし） | Teacher のみ | 不要 | 不要 |
| `opd-job.yaml`（Reward のみ保持） | Teacher + Reward | 不要 | 必要 |
| `opd-job.yaml`（Rollout のみ保持） | Teacher + Rollout | 必要 | 不要 |
| `opd-job.yaml`（両方のブロックを保持） | Teacher + Rollout + Reward | 必要 | 必要 |

### 3.2 トレーニングデータの準備

`data` ディレクトリ以下にデータセットファイルを追加します：

- `data/calc_training_min.jsonl` - トレーニングデータセット（JSONL 形式）
- `data/calc_validation_min.jsonl` - 検証データセット（JSONL 形式）

## 4. SDK によるタスクの実行

### 4.1 関数の実行（登録 + テスト）

通常の強化学習トレーニングには、カスタム Rollout と少なくとも1つの
Reward が必要です。OPD では Rollout と Reward はどちらも任意です。

```bash
python test_functions.py
```

### 4.2 ワークフローの実行（YAML 設定 + ライフサイクル管理）

通常の強化学習トレーニングと OPD は同じ SDK ワークフローを使用します。
対応する YAML を選択してください：

```python
from dashscope.finetune.agentic_rl import AgenticRL

client = AgenticRL()
# 通常の強化学習には rl-job.yaml、OPD には opd-job.yaml を使用
client.init(config_path="rl-job.yaml")
result = await client.run()
```

`opd-job.yaml` はデフォルトで両方の関数ブロックを保持しており、
Teacher + Rollout + Reward を表します。Reward ブロックを削除すると
Teacher + Rollout に、Rollout ブロックを削除すると Teacher + Reward に、
両方を削除すると Teacher のみになります。

```bash
# submit_job.py はデフォルトで通常の強化学習用 rl-job.yaml を使用します
python submit_job.py
```

## 5. CLI によるタスクの実行
サンプルコード：cli.sh

`cli.sh` は通常の強化学習ワークフローを示しています。OPD の場合は、
`opd-job.yaml` から削除された関数ブロックについて登録とテストを
スキップしてください。データセットのアップロード、`rl run`、ジョブの
ライフサイクル管理コマンドはそのまま変わりません。

CLI は SDK と同じ YAML ファイルを使用します：

```bash
# 通常の強化学習
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml

# opd-job.yaml に設定された Teacher を上書き
dashscope rl run -c opd-job.yaml \
  --teacher-model qwen3.5-397b-a17b
```

```bash
dashscope rl --help  # コマンドヘルプ全体を表示

 Usage: dashscope [OPTIONS] COMMAND [ARGS]...

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ get                 📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## ベストプラクティス

1. **開発・テスト**：提出前に `test_functions` コマンドで関数ロジックを検証する
2. **インクリメンタルな開発**：変更後は関数を再登録するだけでよく、環境全体を再構築する必要はない
3. **ログによるトラブルシューティング**：`LOG_LEVEL=debug` を設定して詳細なデバッグ情報を取得する
4. **リソース管理**：タスク完了後は `delete` コマンドでリソースを解放する

> 注：すべてのパスとパラメータは実際のプロジェクトに合わせて調整してください。サンプルスクリプトはプロジェクトの `workspace/` ディレクトリにあります
>
> 注：プロジェクトの `workspace/` ディレクトリ以下のすべてのファイルはパッケージ化されてクラウドにアップロードされ、オンライン計算に使用されます。データのセキュリティにご注意ください
>
> 注：プロジェクトの `workspace/` ディレクトリ以下でアップロード対象から除外するサブディレクトリ・ファイルを設定するには、環境変数 `FC_ZIP_EXCLUDE_PATTERNS` を参照してください
>
> 注：プロジェクトの `workspace/` ディレクトリ以下の全ファイルをパッケージ化・アップロードする際の合計サイズ上限はデフォルトで 200M です。環境変数 `FC_OSS_FILE_SIZE_WARNING` で変更できます
>
> 注：単一のデータセットファイル（トレーニング/検証用 JSONL など）の最大サイズはデフォルトで 1G です。環境変数 `DATASETS_FILE_SIZE_WARNING` で変更できます
>
> 注：ローカルでビルドした dashscope の whl パッケージ（`scripts/build.sh` スクリプトで生成）を使用したい場合は、次のように設定します：
> export FC_PYPI_LIB="dashscope-1.25.19-py3-none-any.whl"
> そして、それをプロジェクトルート以下の workspace/workspace/ ディレクトリに配置してください。あわせて `requirements.txt` から dashscope の依存関係を削除してください。
