# Agentic Reinforcement Learning: ユーザーガイド [[English]](./UserGuide.md) [[中文]](./UserGuide-zh.md)

---

## 1. はじめに

**Agentic RL SDK/CLI** は、大規模言語モデル（LLM）向けの強化学習（RL）モデルを構築・トレーニング・管理するための包括的なツールチェーンを提供します。エージェントの振る舞いを定義し、トラジェクトリ（軌跡）を収集し、ポリシーを最適化するという複雑なワークフローを簡素化します。

SDK は 2 つのコアモジュールで構成されています：
1.  **Functions モジュール**：**Rollout**（トラジェクトリ生成）、**Reward**（スコアリング）、**Group Reward**（バッチスコアリング）用のカスタム Python コードを管理します。自動登録・テスト、および組み込みの**可観測性（Tracing）**をサポートします。
2.  **Tuning モジュール**：データセット管理、ハイパーパラメータ設定、ジョブの投入、ライフサイクル管理（ステータス、ログ、キャンセル）を扱います。

**ワークフロー**：
1. カスタム関数を登録します。通常の強化学習トレーニングには Rollout と
   少なくとも1つの Reward が必要です。OPD では Rollout と Reward はどちらも任意です。
2. Tuning モジュールを使ってデータセットをアップロードし、ジョブを設定して
   トレーニングに投入します。

---

## 2. インストールとセットアップ

### 2.1 PyPI からインストール
```bash
pip install dashscope>=1.25.19
```

### 2.2 ソースからインストール（開発用）
```bash
git clone https://github.com/dashscope/dashscope-sdk-python.git
cd dashscope-sdk-python
pip install -e .  # 開発用に editable モードでインストール
```

### 2.3 認証
1.  **DashScope API Key** を取得します。
2.  環境変数を設定します：
    ```bash
    export DASHSCOPE_API_KEY='your-api-key-here'
    ```

### 2.4 プロジェクト構成
以下の推奨ワークスペース構成により、スムーズなデプロイとローカルテストが可能になります：

```text
workspace/
├── data/                   # データセット
│   ├── training.jsonl
│   └── validation.jsonl
├── functions/              # カスタム関数。OPD の場合のみ省略可能
│   ├── reward/
│   │   ├── group_reward.py
│   │   └── reward.py
│   └── rollout/
│       └── rollout.py
├── requirements.txt        # Function コンポーネントの依存関係
├── rl-job.yaml             # 通常の Agentic RL 設定
└── opd-job.yaml            # OPD 設定
```

通常の強化学習トレーニングには、カスタム Rollout と少なくとも1つの
Reward が必要です。Rollout と Reward を省略したり、どちらか一方だけを
単独で設定できるのは OPD のみです。

### 2.5 依存パッケージ（requirements.txt のガイドライン）
このファイルは Function コンポーネントをクラウドにデプロイする際に**必須**です。ワークスペースのルートに配置する必要があります。

**requirements.txt:**
```txt
fastapi==0.136.0
uvicorn==0.45.0
typer==0.24.1
rich==15.0.0
pyyaml==6.0.3
protobuf>=4.25.8,<7.0 #6.33.6
fsspec==2026.3.0
httpx==0.28.1
tenacity==9.1.4
```

**主な注意点：**
*   **デフォルトのパッケージ**：`dashscope` はランタイム環境にあらかじめインストールされています。`requirements.txt` に含めないでください。
*   **Protobuf**：互換性の問題を避けるため、指定されたバージョン範囲内である必要があります。

#### 可観測性（Tracing）のための依存関係
可観測性のスパン（processor / LLM / tool）を使用するには、`requirements.txt` に以下の依存関係を追加してください（再現可能なデプロイのため、バージョン固定を推奨します）：

```txt
opentelemetry-api==1.41.1
opentelemetry-sdk==1.41.1
opentelemetry-exporter-otlp-proto-http==1.41.1
opentelemetry-processor-baggage==0.62b1
loongsuite-util-genai==0.4.0
```

### 2.6 ロギング設定
`LOG_LEVEL` 環境変数でログの詳細度を設定します：

```bash
export LOG_LEVEL="DEBUG"   # 最も詳細（API キーなどの機密情報はマスクされます）
export LOG_LEVEL="INFO"    # デフォルト
export LOG_LEVEL="WARNING"
export LOG_LEVEL="ERROR"
export LOG_LEVEL="CRITICAL"
```

---

## 3. 関数の実装

参照：workspace/functions ディレクトリ、出力先は rollout.py、reward.py など

### 3.1 関数の実装

関数は SDK が提供する抽象基底クラスを継承する必要があります。

#### Rollout プロセッサ
エージェントのトラジェクトリ（環境／LLM とのやり取り）を生成します。

```python
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput

class DemoRolloutProcessor(AbstractRolloutProcessor):
    async def process(self, input: RolloutInput) -> RolloutOutput:
        # トラジェクトリを生成する（async/def どちらもサポート）
        pass
```

#### Reward プロセッサ
個々のステップまたは最終出力をスコアリングします。

```python
from dashscope.finetune.reinforcement import AbstractRewardProcessor, RewardInput, RewardOutput

class DemoRewardProcessor(AbstractRewardProcessor):
    def process(self, input: RewardInput) -> RewardOutput:
        # 報酬スコアを計算する
        pass
```

#### デコレーターを使った高度な Reward プロセッサ
```python
from dashscope.finetune.reinforcement import reward_func, sub_reward_func, aggregate_func

@reward_func("SafetyProcessor")
class SafetyProcessor(AbstractRewardProcessor):
    @sub_reward_func("toxicity", sub_weight=0.7)
    def toxicity(self, input: RewardInput) -> RewardOutput: ...

    @sub_reward_func("refusal", sub_weight=0.3)
    async def refusal(self, input: RewardInput) -> RewardOutput: ...

    @aggregate_func
    async def aggregate(self, sub_rewards: dict[str, RewardOutput]) -> RewardOutput: # カスタム集約ロジック
        weights = self.get_weights()
        scores = self.get_scores(sub_rewards)
        reward_metrics = self.get_reward_metrics(sub_rewards)

        total = ...  # 合計報酬を計算する
        return RewardOutput(...)
```

#### Group Reward プロセッサ
複数のトラジェクトリをまとめてスコアリングします（例：ランキング用途）。

```python
from dashscope.finetune.reinforcement import AbstractGroupRewardProcessor, GroupRewardInput, GroupRewardOutput

class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    def setup(self) -> None:
        pass

    async def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        # グループ報酬を計算する
        pass
```

### 3.2 可観測性（Tracing）

OpenTelemetry を使って、エージェントの実行状況を詳細に可視化できます。コンソールで ARMS 認可を完了すると、トレースデータは **ARMS**（アリババクラウド リアルタイムモニタリングサービス）にエクスポートされます。詳細は [ARMS ドキュメント](https://help.aliyun.com/zh/arms/?spm=5176.30275541.J_ZGek9Blx07Hclc3Ddt9dg.3.3ce02f3dmKOpPK&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@596792.S_new~UND~card.ID_card@@%E4%BA%A7%E5%93%81@@596792-RL_arms-LOC_2024SPSearchCard-OR_ser-PAR1_0bc1409817757870159831522e3953-V_4-RE_new5-P0_0-P1_0) を参照してください。

#### 前提条件
1.  可観測性の依存関係を `requirements.txt` に追加してください（セクション 2.5「可観測性（Tracing）のための依存関係」を参照）。

#### インストルメンテーション用デコレーター
`dashscope.finetune.reinforcement.component.observability` からインポートします。

| デコレーター | 使用場所 | 説明 |
| :--- | :--- | :--- |
| `@observe_processor` | `process()` メソッド上 | 入出力・レイテンシ・ステータスを自動的にトレースします。span の種類（ROLLOUT/REWARD）も自動判定します。 |
| `trace_client()` | `setup()` 内、または最初の LLM 呼び出しの前 | LLM クライアント（OpenAI、DashScope、LangChain ライク）をラップします。以降のすべての呼び出しを自動的にトレースします。**推奨**。 |
| `@observe_llm` | カスタム LLM 関数上 | `trace_client` がお使いのラッパーに対応していない場合に使用します。`model` と `messages` をキーワード引数として渡す必要があります。 |
| `trace_tool()` | `setup()` 内（ツール作成後） | ツール（LangChain/MCP/LangGraph ライク）をラップします。ツール呼び出しを自動的にトレースします。 |
| `@observe_tool` | 通常の関数上 | BaseTools としてラップされていない単純な Python 関数に使用します。 |

> **Setup：** サーバー起動時に一度だけ呼び出されます。同期・非同期の両方に対応しています。同期の setup はイベントループをブロックしないようオフロードされます。

#### `trace_client()` がサポートするもの（ダックタイピング）
`trace_client(client)` はクラス名ではなく構造によって判定されます。以下をサポートします：

- **完全な OpenAI クライアント**（`.chat.completions.create` を公開しているもの）
- **Completions リソース**（`.create` を公開し `.chat` を持たないもの、例：`ChatOpenAI.client`）
- **LangChain ライクなラッパー**（`.client` および/または `.async_client` を公開しているもの）
- **DashScope の Generation クラス**（クラス自体を渡します。`call` がクラスメソッドとして存在します）

#### `trace_tool()` がサポートするもの
`trace_tool(tools)` は以下の形式を受け付けます：

- 単一のツールオブジェクト（例：LangChain の `BaseTool`）
- ツールのリスト／タプル
- 名前とツールをマッピングした辞書
- LangGraph の `ToolNode`（内部でツールが展開されます）
- `langchain-mcp-adapters` が返す MCP ツール（provider は自動的に `"mcp"` に設定されます）

> **MCP に関する注意：** MCP のサーバーとクライアントは別プロセスで動作します。サーバー側の関数に `@observe_tool` を付けても、クライアント側には影響しません。クライアント側では、必ず `get_tools()` の後に `trace_tool(tools)` を呼び出してください。

#### 例：インストルメント化された Rollout プロセッサ

```python
import openai
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput
from dashscope.finetune.reinforcement.component.data.base_data_model import AgentOutput, TaskStatus
from dashscope.finetune.reinforcement.component.observability import (
    observe_processor,
    trace_client,
    trace_tool,
)

class MyRolloutProcessor(AbstractRolloutProcessor):

    async def setup(self) -> None:
        # 1. LLM クライアントをトレース
        self._client = openai.AsyncOpenAI(base_url="...", api_key="...")
        trace_client(self._client)

        # 2. ツールをトレース（例：MCP）
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({...})
        self._tools = await client.get_tools()
        trace_tool(self._tools)

    @observe_processor
    async def process(self, input: RolloutInput) -> RolloutOutput:
        messages = input.messages or []
        model = input.model_resource.model_name

        # trace_client(self._client) により、この呼び出しは自動的にトレースされます
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )

        content = response.choices[0].message.content if response.choices else ""

        return RolloutOutput(
            agent_output=AgentOutput(messages=messages, reward_score=0.0),
            status=TaskStatus.SUCCESS,
        )
```

---

## 4. SDK / CLI リファレンス
* [SDK] インターフェースクラス：dashscope.finetune.agentic_rl.AgenticRL
* [CLI] エントリーポイント：dashscope rl

### 4.1 ジョブ設定

通常の強化学習トレーニングと OPD は、同じ SDK/CLI ワークフローを使用します。
対応する YAML 設定を選択してください。コードで指定した引数は YAML の値より優先されます。

| トレーニング種別 | 設定ファイル | カスタム関数 |
|---|---|---|
| 通常の強化学習 | `rl-job.yaml` | Rollout は必須、Reward は少なくとも1つ必要 |
| OPD | `opd-job.yaml` | Rollout と Reward はそれぞれ独立して任意で、両方省略も可能 |

**[SDK] \_\_init\_\_**
```python
def __init__(self, api_key: str = None): ...
```
AgenticRL インスタンスを初期化します。

**パラメータ**：
- `api_key`：認証用の API キー（指定しない場合は環境変数を使用）

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL(api_key="your_api_key")
```

**[SDK] [init](submit_job.py)**
```python
def init(self, config_path: Optional[str] = None, **kwargs) -> Self: ...
```
YAML 設定ファイルからインスタンスを初期化します。

**パラメータ**：
- `config_path`：YAML 設定ファイルのパス
- `**kwargs`：設定の上書き

**戻り値**：Self インスタンス

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL
config_path = "opd-job.yaml"  # 通常の強化学習には "rl-job.yaml" を使用
rl = AgenticRL().init(config_path, job_name="custom_job")
result = await rl.run()
```

`opd-job.yaml` を選択した場合、Rollout と Reward のブロックを保持または
削除することで、必要な機能を選択します：

| 保持する関数ブロック | OPD モード | トラジェクトリの供給元 | タスク報酬 |
|---|---|---|---|
| どちらもなし | Teacher のみ | プラットフォーム | 無効 |
| Reward のみ | Teacher + Reward | プラットフォーム | カスタム Reward |
| Rollout のみ | Teacher + Rollout | カスタム Rollout | 無効 |
| Rollout と Reward | Teacher + Rollout + Reward | カスタム Rollout | カスタム Reward |

コミットされている `opd-job.yaml` は両方のブロックを保持しています。他の
OPD の組み合わせを選択するには、どちらか一方または両方のブロックを削除してください：

```yaml
teacher_model: qwen3.5-397b-a17b

functions:
# このブロックを削除するとプラットフォーム生成を使用します。
- type: rollout
  # ...
# このブロックを削除するとカスタムタスク報酬を無効化します。
- type: reward
  # ...

training:
  type: pg_opd
```

```bash
# 通常の強化学習
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml
```

### 4.2 関数の登録

コードをアップロードし、Function コンポーネント（関数）を登録します。

**[SDK] [register_functions](submit_job.py)**
```python
def register_functions(self, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None, lazy_load: Optional[bool] = True) -> tuple: ...
```
Function コンポーネントを登録します。

**パラメータ**：
- `functions`：登録する Function コンポーネント
- `lazy_load`：実行時までロードを遅延させる

**戻り値**：entity/instance ID のタプル

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()
rollout_eids, reward_eids, group_eids, \
rollout_iids, reward_iids, group_iids = await rl.register_functions(
    functions=[
        AgenticRLFunctionComponent(
            type=FunctionType.ROLLOUT,
            fcmodel=FunctionComponentModel(
                zipdir='./',
                classpath="functions.rollout.rollout2.DemoRolloutProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions/reward/reward.py:DemoRewardProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.GROUP_REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions.reward.group_reward.DemoGroupRewardProcessor"),
        ),
    ],
    lazy_load=False  # テストのためすぐに instance ID を取得したい場合は False にする
)
```

**[CLI] register_functions**

**使い方: dashscope register_functions [OPTIONS]**
```bash
 🧩 Register Rollout/Reward function components, returns entity_id & instance_id

 Requires at least one of:
 - rollout_classpath
 - reward_classpaths

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --rollout-classpaths                             TEXT  List for rollout class path (file.py:ClassName)                                                                                                               │
│ --reward-classpaths                              TEXT  List for reward class path (file.py:ClassName)                                                                                                                │
│ --group-reward-classpaths                        TEXT  List for group-reward class path (file.py:ClassName)                                                                                                          │
│ --workspace-dir                                  TEXT  Local workspace directory [default: ./]                                                                                                                       │
│ --lazy-load                    --no-lazy-load          Delay instance loading (set False for debugging) [default: lazy-load]                                                                                         │
│ --api-key                                        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                    │
│ --output-format            -o                    TEXT  Output format: table|json|yaml [default: json]                                                                                                                │
│ --help                                                 Show this message and exit.                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**例**：
```bash
dashscope rl register_functions \
  --rollout-classpath "functions.rollout.rollout2.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.group_reward.DemoGroupRewardProcessor" \
  --workspace-dir "./" \
  --output-format json
```

### 4.3 関数のテスト

#### 4.3.1 リモートテスト
**[SDK] [test_functions](test_functions.py)**

登録済みのインスタンスをサンプルデータでテストします。

```python
def test_functions(cls, instance_id: str, type: FunctionType, input_data: Dict[str, Any], api_key: str = None): ...
```

**パラメータ**：
- `instance_id`：Function インスタンス ID
- `type`：関数の種類（ROLLOUT/REWARD/GROUP_REWARD）
- `input_data`：テスト用の入力データ
- `api_key`：認証用の API キー

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL, FunctionType

# Rollout をテスト
result = await AgenticRL.test_functions(
    instance_id=rollout_iids[0],
    functype=FunctionType.ROLLOUT,
    input_data="resouces/rollout_input.json" # JSON ファイルへのパス
)

# Reward をテスト
reward_input = {
    "func_type": "reward",
    "agent_output": {
        "messages": [{"role": "user", "content": "Test"}],
        "reward_score": null
    }
}
result = await AgenticRL.test_functions(
    instance_id=reward_iids[0],
    functype=FunctionType.REWARD,
    input_data=reward_input
)
```

**[CLI] test_functions**

**使い方: dashscope test_functions [OPTIONS] INSTANCE_ID**
```bash
 🧪 Test a registered Rollout/Reward function instance with custom input data.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    instance_id      TEXT  Target function instance ID (e.g., ro-ins-xxx or rw-ins-xxx) [required]                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --type           -t      TEXT  Function type: ROLLOUT or REWARD [required]                                                                                                                                        │
│ *  --input          -i      TEXT  JSON string or file path containing test payload [required]                                                                                                                        │
│    --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│    --output-format  -o      TEXT  Output format: table|json|yaml [default: json]                                                                                                                                     │
│    --help                         Show this message and exit.                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**例**：
```bash
dashscope rl test_functions "ro-ins-xxx" \
  --type rollout \
  --input "resources/rollout_input.json"
```

### 4.4 ワンステップ・ワークフロー
関数の登録、データのアップロード、ジョブの投入を自動的に行います。

**[SDK] [run](submit_job.py)**
```python
async def run(
    self,
    model: Optional[str] = None,
    training_datasets: Optional[List[TrainingDataset]] = None,
    validation_datasets: Optional[List[ValidationDataset]] = None,
    functions: Optional[
        Union[List[AgenticRLFunctionComponent], AgenticRLFunctionComponent]
    ] = None,
    hyper_parameters: Optional[Dict[str, str]] = None,
    resources: Optional[Dict[str, str]] = None,
    job_name: Optional[str] = None,
    teacher_model: Optional[str] = None,
    **kwargs,
) -> FineTune: ...
```
一連のワークフローを実行します（登録 + アップロード + 投入）。

**パラメータ**：
- `model`：ベースモデル名
- `training_datasets`：トレーニングデータセットオブジェクト
- `validation_datasets`：検証データセットオブジェクト
- `functions`：Function コンポーネント
- `hyper_parameters`：トレーニングのハイパーパラメータ
- `resources`：トレーニングのリソース設定
- `job_name`：カスタムジョブ名
- `teacher_model`：Teacher モデル。指定すると OPD が有効になり、Rollout と Reward は任意になります

**戻り値**：`FineTune` ジョブオブジェクト

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()
rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 2,
                    "env": {}, "capacity": 5}
reward_runtimes = [
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 10, "env": {},
     "capacity": 8},
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 5, "env": {},
     "capacity": 6}
]
functions=[
    RolloutFunctionComponent(
        type=FunctionType.ROLLOUT,
        name="rollout-1",
        fcmodel=FunctionComponentModel(
            classpath="functions.rollout.rollout_only.DemoRolloutProcessor"),
        runtime=FunctionComponentRuntime(**rollout_runtime)),
    AgenticRLFunctionComponent(
        type=FunctionType.REWARD,
        name="reward-1",
        weight=1.0,
        fcmodel=FunctionComponentModel(
            classpath="functions.reward.reward.DemoRewardProcessor"),
        runtime=FunctionComponentRuntime(**reward_runtimes[0])),
]
training_datasets=[
    TrainingDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_train_min.jsonl",
    ),
]
validation_datasets=[
    ValidationDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_validation_min.jsonl",
    ),
]
job = await rl.run(
    model="qwen3.5-9b",
    training_datasets=training_datasets,
    validation_datasets=validation_datasets,
    functions=functions,
    hyper_parameters={'batch_size': '128'}
)
```

**[CLI] run**

**使い方: dashscope rl run [OPTIONS]**
```bash
 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)

 Execution modes:
 1. Configuration-driven: Use -c/--config to specify a YAML file
 2. Direct parameter: Provide all required arguments via CLI options

 Required parameters:
 - training_files (at least one)
 - Rollout and Reward are required for reinforcement learning, but optional for OPD.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                   -c      PATH   Path to YAML configuration file                                                                                                                                            │
│ --model                            TEXT   Base model identifier                                                                                                                                                      │
│ --teacher-model                    TEXT   Enable OPD and override the Teacher model in YAML; Rollout and Reward are optional                                                                                          │
│ --training-files                   TEXT   Paths to training dataset files                                                                                                                                            │
│ --validation-files                 TEXT   Paths to validation dataset files                                                                                                                                          │
│ --rollout-classpath                TEXT   Python import path to rollout class (module:Class)                                                                                                                         │
│ --reward-classpaths                TEXT   List for reward class path (file.py:ClassName)                                                                                                                             │
│ --group-reward-classpaths          TEXT   List for group-reward class path (file.py:ClassName)                                                                                                                       │
│ --rollout-name                     TEXT   Pre-registered Rollout entity_name                                                                                                                                         │
│ --reward-names                     TEXT   Comma-separated list of reward entity_names                                                                                                                                │
│ --group-reward-names               TEXT   Comma-separated list of group-reward entity_names                                                                                                                          │
│ --rollout-weight                   TEXT   Pre-registered Rollout entity_weight                                                                                                                                       │
│ --reward-weights                   FLOAT  Comma-separated list of reward entity_weights                                                                                                                              │
│ --group-reward-weights             FLOAT  Comma-separated list of group-reward entity_weights                                                                                                                        │
│ --reward-metric-weights            TEXT   Reward metric weights as JSON string (list of dicts)                                                                                                                       │
│ --rollout-runtime                  TEXT   Rollout runtime as JSON string                                                                                                                                             │
│ --reward-runtimes                  TEXT   Reward runtimes as JSON string                                                                                                                                             │
│ --group-reward-runtimes            TEXT   Group-reward runtimes as JSON string                                                                                                                                       │
│ --hyper-parameters                 TEXT   JSON string of hyper_parameters                                                                                                                                            │
│ --job-name                         TEXT   Custom name for the tuning job                                                                                                                                             │
│ --api-key                          TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                 │
│ --workspace-dir                    TEXT   Workspace directory for job artifacts [default: ./]                                                                                                                        │
│ --output-format            -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                            │
│ --verbose                  -v             Enable detailed error traces                                                                                                                                               │
│ --help                                    Show this message and exit.                                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**例**：フルワークフローの実行（自動）
```bash
dashscope rl run \
  --config "rl-job.yaml" \
  --verbose
```

### 4.5 ジョブ管理

**[SDK] get**
```python
def get(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
ジョブ情報を取得します。

**パラメータ**：
- `job_id`：取得対象のジョブ ID
- `api_key`：認証用の API キー
- `workspace`：ワークスペース識別子

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL
job = AgenticRL.get("job-12345")
```

**[CLI] get**

**使い方: dashscope get [OPTIONS] JOB_ID**
```bash
 📊 Query the current status and metadata of a specific job

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                            │
│ --output-format  -o      TEXT  [default: table]                                                                                                                                                                      │
│ --help                         Show this message and exit.                                                                                                                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**例**：
```bash
dashscope rl get "$JOB_ID" -o json
```

**[SDK] cancel**
```python
def cancel(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneCancel: ...
```
実行中のジョブをキャンセルします。

**パラメータ**：
- `job_id`：キャンセル対象のジョブ ID
- `api_key`：認証用の API キー
- `workspace`：ワークスペース識別子

**例**：
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.cancel("job-12345")
```

**[CLI] cancel**

**使い方: dashscope cancel [OPTIONS] JOB_ID**
```bash
 🛑 Cancel a running job

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                                    │
│ --help                 Show this message and exit.                                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**例**：
```bash
dashscope rl cancel "$JOB_ID"
```

---

## 5. CLI リファレンス

CLI は SDK の機能をそのまま反映しています。詳細は `dashscope rl --help` を実行して確認してください。

### 使い方: dashscope [OPTIONS] COMMAND [ARGS]...
```bash

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ submit              📤 Submit fine-tuning job (requires pre-registered functions & uploaded datasets)                                                                                                                 │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ status              📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 6. FAQ とトラブルシューティング

**Q：関数の登録に失敗する。**
*   **確認**：classpath は正しいですか（`module.path:ClassName`）？
*   **確認**：`requirements.txt` はワークスペースのルートに存在しますか？
*   **確認**：必要な依存関係がすべて `requirements.txt` に記載されていますか？

**Q：ジョブの投入に失敗する。**
*   **確認**：Entity ID と File ID は有効ですか？
*   **確認**：ベースモデルはお使いのリージョンで利用可能ですか？
*   **確認**：`reward_runtimes` のリストの長さは `reward_ids` のリストの長さと一致していますか？

**Q：パフォーマンスを最適化するには？**
*   I/O バウンドなタスクには `async def process` を使用してください。
*   CPU/メモリに余裕があれば、ランタイム設定の `concurrency` を増やしてください。
*   可観測性のペイロードは適切な範囲に収め（入出力の過剰なキャプチャを避け）、オーバーヘッドを減らしてください。

**Q：トレースはどこで確認できますか？**
*   百煉（Bailian）コンソールで ARMS 認可を完了すると、トレースは **ARMS** に送信されます。`requirements.txt` に可観測性の依存関係が含まれていること、および可観測性 API（`observe_processor`、`trace_client`、`trace_tool` など）を使用していることを確認してください。
