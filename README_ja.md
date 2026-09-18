# DashScope Python SDK

> [English](README.md) | [中文](README_zh.md) | **日本語**

DashScope Python SDK は、[Alibaba Cloud Model Studio（百煉／Bailian）](https://www.alibabacloud.com/help/en/model-studio/) の API を包括的に利用できるインターフェースを提供します。テキスト生成、マルチモーダル理解、Embedding（埋め込み）、リランキング、画像・動画生成、音声合成・音声認識など、幅広い機能をカバーしています。

## 最新情報

**v1.27.0 でインタラクティブな AI アシスタントを搭載しました —— [DashScope SDK Expert](#ai-アシスタントdashscope-sdk-expert)。** 引数を付けずに `dashscope` を実行する（または `dashscope "how do I stream Generation output"` のように直接質問する）だけで、ターミナル上で SDK/API に関する回答、実行可能なサンプルコード、CLI の使い方、エラー診断を得られます。案内内容は、SDK の公開インターフェース（パラメータ、出力、エラーコード）に基づくドメイン別のクイックリファレンススキル（テキスト、マルチモーダル、音声、検索、ファインチューニング、エージェント、CLI）から生成されるため、ドキュメントを読む代わりに質問するだけで済みます。アシスタント内で `/help` と入力すると利用可能なコマンドを確認できます。

## インストール

DashScope Python SDK をインストールするには、次を実行するだけです。
```shell
pip install dashscope
```

基本インストールには、SDK の API 呼び出しと `dashscope` CLI コマンドが含まれます。
オプション機能グループは extras として提供されています。

| Extra | 提供する機能 | インストールコマンド |
|-------|----------|---------|
| `acli` | インタラクティブ AI アシスタント（DashScope SDK Expert） | `pip install "dashscope[acli]"` |
| `rl` | Agentic RL ファインチューニング | `pip install "dashscope[rl]"` |
| `tokenizer` | ダウンロード不要のローカル tokenizer | `pip install "dashscope[tokenizer]"` |

GitHub からソースコードを clone した場合は、ソースからインストールできます。
```shell
pip install -e .
```


## クイックスタート

```python
# pip install dashscope
from http import HTTPStatus
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"},
    ],
    result_format="message",
)

if responses.status_code == HTTPStatus.OK:
    print(responses.output.choices[0].message.content)
else:
    print(f"Error: {responses.code} - {responses.message}")
```

### ストリーミング出力

`stream=True` を指定すると、逐次的なレスポンスを返すジェネレータが得られます。`incremental_output=True` を指定すると、各チャンクにはこれまでの累積テキストではなく、新しく生成されたトークンのみが含まれます。

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "海についての俳句を書いてください。"}],
    result_format="message",
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content, end="")
```

### 非同期（asyncio）

`call` ベースの各クラスには、同じパラメータを持つ `Aio` プレフィックス付きの非同期版が用意されており（`AioGeneration`、`AioImageSynthesis`、`AioMultiModalConversation`、`AioVideoSynthesis`、`AioMultiModalEmbedding`、`AioTextReRank` など）、`await` で利用します。

```python
import asyncio
from dashscope import AioGeneration

async def main():
    response = await AioGeneration.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": "Who are you?"}],
        result_format="message",
    )
    print(response.output.choices[0].message.content)

asyncio.run(main())
```

### エラーハンドリング

必須パラメータが不足している場合（`model` が未指定、`messages`/`prompt` が未指定、API キー未設定など）は、その場で `DashScopeException` のサブクラスが送出されます。一方、モデル名が不正、レート制限超過などの API レベルの失敗は例外にはならず、レスポンスに含まれて返されるため、`status_code` を確認する必要があります。

```python
from http import HTTPStatus
from dashscope import Generation
from dashscope.common.error import DashScopeException

try:
    response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
except DashScopeException as e:
    # 入力が不正な場合にローカルで送出される（例: InputRequired、ModelRequired、AuthenticationError）
    print(f"Invalid request: {e}")
else:
    if response.status_code != HTTPStatus.OK:
        # API から返されるエラー（例: モデル名が不正、レート制限、クォータ超過）
        print(f"API error {response.status_code}: {response.code} - {response.message}")
    else:
        print(response.output.choices[0].message.content)
```

## API Key 認証

このSDKは API Key を使用して認証を行います。API Key の取得方法については、[API Key の取得方法](https://help.aliyun.com/en/model-studio/get-api-key) を参照してください。取得手順の詳細は、[Alibaba Cloud 公式ドキュメント（中国国内版）](https://www.alibabacloud.com/help/en/model-studio/) および [Alibaba Cloud 公式ドキュメント（国際版）](https://www.alibabacloud.com/help/en/model-studio/) を参照してください。

### API Key の使用方法

1. コードから API Key を設定する
```python
import dashscope

dashscope.api_key = 'YOUR-DASHSCOPE-API-KEY'
# または、コードから API Key ファイルのパスを指定する
# dashscope.api_key_file_path='~/.dashscope/api_key'

```

2. 環境変数から API Key を設定する

```shell
# a. API Key を直接設定する
export DASHSCOPE_API_KEY='YOUR-DASHSCOPE-API-KEY'

# b. または、API Key を含むファイルのパスを指定する
export DASHSCOPE_API_KEY_FILE_PATH='~/.dashscope/api_key'
```

いずれかの環境変数を設定しておけば、`Generation.call(...)`（および他のすべての SDK 呼び出し）は `api_key=` 引数を渡さなくても自動的にキーを読み込みます。

```python
from dashscope import Generation

# DASHSCOPE_API_KEY（または DASHSCOPE_API_KEY_FILE_PATH）が自動的に読み込まれる
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

3. API Key をファイルに保存する
```python
from dashscope import save_api_key

save_api_key(api_key='YOUR-DASHSCOPE-API-KEY',
             api_key_file_path='api_key_file_location or (None, will save to default location "~/.dashscope/api_key"')

```

## リージョンとエンドポイントの設定

デフォルトでは、SDK は中国（北京）のパブリックエンドポイント `dashscope.aliyuncs.com` にリクエストを送信します。お使いの Model Studio（百煉）のワークスペースが別のリージョンにある場合は、呼び出しを行う前にエンドポイントを切り替えてください。

### `set_region` を使用する

`dashscope.set_region(region, workspace_id)` は、HTTP・WebSocket・OpenAI 互換の各ベース URL を、一度の呼び出しで指定したリージョンに向けます。`workspace_id` は必須で、エンドポイントのサブドメインとして使用されます。

```python
import dashscope

# ワークスペース "ws-xxx123" 用にシンガポールリージョンへ切り替える
dashscope.set_region(region="ap-southeast-1", workspace_id="ws-xxx123")

# 以降のすべての呼び出しは次を使用する:
#   https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
print(dashscope.base_http_api_url)
```

サポートされているリージョン:

| リージョン | 所在地 |
|--------|----------|
| `cn-beijing` | 中国（北京） |
| `cn-hongkong` | 中国（香港） |
| `ap-southeast-1` | シンガポール |
| `ap-northeast-1` | 日本（東京） |
| `eu-central-1` | ドイツ（フランクフルト） |
| `us-east-1` | 米国（バージニア） |

> **API Key はリージョンごとに異なります。** 各リージョンの API Key（`sk-` プレフィックス）は、そのリージョンの Model Studio コンソールで発行され、リージョンをまたいで併用することはできません。別リージョンの Key を使用すると `401` エラーになります。リージョンを切り替える際は `api_key` も合わせて変更してください。

リージョン固有の注意事項:

- WebSocket エンドポイント（`wss://.../api-ws/v1/inference`）は、現在 `cn-beijing` と `ap-southeast-1` でのみ提供されています。`set_region` はすべてのリージョンで `base_websocket_api_url` を設定しますが、WebSocket ベースのリアルタイム API（リアルタイム音声認識/合成、マルチモーダル対話など）は他のリージョンでは利用できません。
- `eu-central-1` / `ap-northeast-1`：デプロイのスコープ（グローバル、または EU / 日本）は、コンソールでワークスペースを作成する際に選択するものであり、API 呼び出しごとに指定するものではありません。
- `us-east-1`：`-us` サフィックス付きのモデル名（例: `qwen-plus-us`）は推論を米国内に限定します。サフィックスなしの場合はデフォルトでグローバル推論になります。
- バッチ推論、モデルのファインチューニング、アプリケーション開発は、現時点では `cn-beijing` と `ap-southeast-1` でのみ利用可能です。

> `set_region` はプロセス全体のグローバル変数を更新するため、単一プロセスで複数のリージョンに同時にアクセスする場合、並行実行に対して安全ではありません。起動時に一度だけ呼び出すか、切り替えるたびに再度呼び出してください。

### 環境変数を使用する

コードを書かずに、環境変数だけでリージョンを選択することもできます。

```shell
export DASHSCOPE_API_REGION='ap-southeast-1'   # デフォルト: cn-beijing
export DASHSCOPE_WORKSPACE_ID='ws-xxx123'      # エンドポイントのサブドメインの解決に使用
```

```python
import dashscope

# DASHSCOPE_API_REGION / DASHSCOPE_WORKSPACE_ID が自動的に読み込まれる
print(dashscope.base_http_api_url)
# https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
```

`DASHSCOPE_API_REGION` によって MaaS リージョンが設定されている場合、SDK は対応するリージョンのエンドポイントを構築し、`DASHSCOPE_WORKSPACE_ID` をそこに代入します。各ベース URL を直接上書きすることも可能です。

| 環境変数 | 上書き対象 |
|----------------------|-----------|
| `DASHSCOPE_HTTP_BASE_URL` | HTTP エンドポイント（`dashscope.base_http_api_url`） |
| `DASHSCOPE_WEBSOCKET_BASE_URL` | WebSocket エンドポイント（`dashscope.base_websocket_api_url`） |
| `DASHSCOPE_COMPATIBLE_BASE_URL` | OpenAI 互換エンドポイント（`dashscope.base_compatible_api_url`） |

`set_region` が構築するのは常にワークスペース専用のエンドポイントです。一部のリージョンでは、ワークスペースのサブドメインを持たない共有ドメインも提供されています —— 北京の `dashscope.aliyuncs.com`、シンガポールの `dashscope-intl.aliyuncs.com`、米国バージニアの `dashscope-us.aliyuncs.com` です。これらを使用する場合は、上記の環境変数で直接上書きしてください。

### OpenAI 互換のチャット補完

SDK には、`dashscope.base_compatible_api_url`（リクエストパス `chat/completions`）にアクセスする OpenAI 互換のチャット補完エンドポイントが用意されています —— 追加で `openai` パッケージをインストールする必要はありません。上記で設定したリージョンに従って動作します。

```python
import dashscope
from dashscope.aigc.chat_completion import Completions

dashscope.set_region(region="cn-hongkong", workspace_id="ws-hk-789")

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hello"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    stream=False,  # True にすると ChatCompletionChunk のジェネレータが返る
)
print(response)
```

完全に実行可能なサンプルは [`samples/set_region_example.py`](samples/set_region_example.py) にあります。

## AI アシスタント：DashScope SDK Expert

このSDKには、バンドルされている Agentic CLI（`dashscope/acli`）フレームワーク上に構築されたインタラクティブ AI アシスタント **DashScope SDK Expert** が同梱されています。DashScope の SDK/CLI を利用するユーザーにとって、開発相談や AI によるコーディング支援を受けるための推奨手段であり、SDK/API に関する質問への回答、実行可能なサンプルコードの生成、CLI の使い方の提示、エラー診断を、ターミナル上でそのまま行えます。

- 引数を付けずに `dashscope` を実行するとアシスタントが起動します。初回起動時には、SDK Expert のナレッジパック（ドメイン別のクイックリファレンススキル：テキスト、マルチモーダル、音声、検索、ファインチューニング、エージェント、CLI）のインストールを提案されます。これにより、ソースコードを読まなくても、SDK の公開インターフェース（パラメータ、出力、エラーコード）に基づいた案内を受けられます
- ドキュメントを読む代わりに質問してください —— 例: `dashscope "how do I stream Generation output"` や `dashscope "CLI command to cancel a fine-tuning job"`。アシスタント内で `/help` と入力すると利用可能なコマンド（`/setup`、`/skill`、`/stats` など）の一覧が表示されます。従来の SDK サブコマンドも引き続き使用でき、認識されないコマンドは自動的にアシスタントに渡されます
- 詳細な使い方: [DashScope SDK Expert ガイド](https://help.aliyun.com/en/model-studio/dashscope-sdk-expert)

## サポートされているモデル

| カテゴリ | 推奨モデル | SDK クラス |
|----------|-------------------|-----------|
| テキスト生成 | qwen3.8-max、qwen3.7-max、qwen3.7-plus、qwen3.6-flash | `Generation` |
| マルチモーダル理解 | qwen3.5-omni-plus、qwen3.7-plus（ビジョン） | `MultiModalConversation` |
| テキスト Embedding | text-embedding-v4、text-embedding-v3 | `TextEmbedding` |
| マルチモーダル Embedding | tongyi-embedding-vision-plus、qwen3-vl-embedding | `MultiModalEmbedding` |
| テキストリランキング | qwen3-rerank、gte-rerank-v2 | `TextReRank` |
| 画像生成 | wan2.7-image-pro、qwen-image-2.0-pro | `ImageSynthesis` |
| 動画生成 | wan2.7-t2v、wan2.7-i2v、happyhorse-1.0-t2v/i2v | `VideoSynthesis` |
| 音声合成（TTS） | cosyvoice-v3.5-plus、cosyvoice-v1 | `SpeechSynthesizer`、`HttpSpeechSynthesizer` |
| 音声認識（ASR） | fun-asr-realtime、fun-asr、paraformer-v1 | `Transcription` |
| オムニ（リアルタイム） | qwen3.5-omni-plus-realtime | `MultiModalConversation` |

最新のモデル一覧は [百煉モデルプラザ（Bailian Model Plaza）](https://bailian.console.aliyun.com/) をご覧ください。

## 使用例

実行可能なサンプルスクリプトは [`samples/`](samples) 以下にも用意されています。

### マルチモーダル理解（ビジョン）

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "この画像には何が写っていますか?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### ローカルファイルの使用

URL を受け付けるすべてのフィールド（messages 内の `image`、`audio`、`video`、`ImageSynthesis` の `images` など）は、ローカルファイルパスもそのまま受け付けます。SDK が自動的に OSS へアップロードするため、手動でヘッダーを設定する必要はありません：

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "/path/to/local/image.jpg"},
        {"text": "この画像には何が写っていますか?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### テキスト Embedding

```python
from dashscope import TextEmbedding

resp = TextEmbedding.call(
    model=TextEmbedding.Models.text_embedding_v3,
    input=["風は強く空は高く猿の声が悲しく響く", "川は澄み砂は白く鳥が舞い戻る"],
    text_type="document",
)
for e in resp.output["embeddings"]:
    print(e["text_index"], e["embedding"][:3])
```

### マルチモーダル Embedding

```python
from dashscope import MultiModalEmbedding

resp = MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"}],
)
print(resp.output)
```

### テキストリランキング

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="中国の首都はどこですか?",
    documents=[
        "中国の首都は北京です。",
        "中国は東アジアにある広大な国です。",
    ],
    return_documents=True,
    top_n=1,
)
for r in resp.output.results:
    print(r.index, r.relevance_score, r.document)
```

### コード生成

`CodeGeneration` は特定のコーディングシーン（`Scenes`）に対応しています：自然言語からのコード生成、コードの説明、コメント生成、コミットメッセージ生成、単体テスト生成、コードに関する質問応答、自然言語から SQL への変換など。

```python
from dashscope import CodeGeneration

response = CodeGeneration.call(
    model=CodeGeneration.Models.tongyi_lingma_v1,
    scene=CodeGeneration.Scenes.nl2code,
    message=[
        {"role": "user", "content": "指定したパス配下の全ファイルの合計サイズを計算する"},
        {"role": "attachment", "meta": {"language": "python"}},
    ],
)
print(response.output)
```

### 画像生成

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="繊細な窓と木製の扉がある花屋",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    for result in rsp.output.results:
        print(result.url)
```

### 動画生成

動画生成は非同期タスクとして実行されます。`call` はタスクが完了するまでブロックします。手動でポーリングしたい場合は `async_call` と `wait`/`fetch` を使用してください。

```python
from http import HTTPStatus
from dashscope import VideoSynthesis

rsp = VideoSynthesis.call(
    model="wan2.7-t2v",
    prompt="月明かりの下を走る子猫",
    audio=True,
    watermark=True,
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output.video_url)
```

### 音声合成（TTS）

Qwen-TTS 系のモデルは `MultiModalConversation` から呼び出し、`messages` の代わりに `text`/`voice` を渡します。

```python
from dashscope import MultiModalConversation

response = MultiModalConversation.call(
    model="qwen3-tts-flash",
    text="Today is a wonderful day to build something people love!",
    voice="Cherry",
    language_type="English",
)
print(response.output.audio.url)
```

CosyVoice 系のモデルは、専用の `SpeechSynthesizer` を使用します。

```python
from dashscope.audio.tts import SpeechSynthesizer

result = SpeechSynthesizer.call(
    model="cosyvoice-v1",
    text="Hello, Bailian.",
    format=SpeechSynthesizer.AudioFormat.format_wav,
)
with open("output.wav", "wb") as f:
    f.write(result.get_audio_data())
```

### ストリーミング音声合成（CosyVoice v2）

テキストを逐次ストリーミングで送信し、生成された音声データをコールバック経由でリアルタイムに受け取ります：

```python
from dashscope.audio.tts_v2 import ResultCallback, SpeechSynthesizer

class Callback(ResultCallback):
    def on_data(self, data: bytes) -> None:
        with open("output.mp3", "ab") as f:
            f.write(data)

synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", callback=Callback())
for text in ["こんにちは、", "これはストリーミング", "音声合成です。"]:
    synthesizer.streaming_call(text)
synthesizer.streaming_complete()
```

### 音声認識（ASR）

`qwen3-asr-flash` などの音声理解モデルは、`MultiModalConversation` から呼び出します。

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [{"audio": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"}],
}]
response = MultiModalConversation.call(
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
)
print(response.output.choices[0].message.content)
```

ファイルベースのバッチ音声認識には `Transcription` を使用します。

```python
from dashscope.audio.asr import Transcription

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
)
if response.output.task_status == "SUCCEEDED":
    print(response.output.results)
```

### ストリーミング音声認識

ライブ／ストリーミング音声ソースの場合、PCM フレームを1つずつ送信し、コールバックで結果を受け取ります（ここではパターンを示すためにファイルをチャンクごとに読み込んでいますが、実際にはライブ音声ソースに置き換えてください）：

```python
from dashscope.audio.asr import Recognition, RecognitionCallback

class Callback(RecognitionCallback):
    def on_event(self, result) -> None:
        print(result.get_sentence())

recognition = Recognition(
    model="paraformer-realtime-v1",
    format="pcm",
    sample_rate=16000,
    callback=Callback(),
)
recognition.start()
with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):
        recognition.send_audio_frame(chunk)
recognition.stop()
```

### 百煉アプリケーション（エージェントアプリ）

[百煉のアプリケーションセンター](https://bailian.console.aliyun.com/) で作成したアプリを呼び出します。

```python
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    app_id="YOUR-APP-ID",
    prompt="このファイルの内容を要約してください",
    stream=True,
    incremental_output=True,
    file_list=["https://example.com/document.pdf"],
)
for response in responses:
    if response.status_code != HTTPStatus.OK:
        print(f"code={response.code}, message={response.message}")
    else:
        print(response.output.text, end="")
```

### AgentStudio（マネージドエージェント）

`dashscope.agentstudio` は、百煉 AgentStudio で構築したエージェントを管理します——エージェント／セッションの作成と会話イベントのストリーミング受信、または cron スケジュールでエージェントを実行する「デプロイメント」の作成です：

```python
from dashscope.agentstudio import Client
from dashscope.agentstudio.types import user_message

client = Client(api_key="sk-xxx")
agent = client.agents.create(name="demo", model="qwen-plus")
session = client.sessions.create(agent=agent.id)
client.sessions.events.send(session.id, [user_message("Hello!")])
with client.sessions.events.stream(session.id) as stream:
    for event in stream:
        print(event.type, event.to_dict())
        if event.type == "session_status":
            break
```

注意：`Client()` は環境変数 `DASHSCOPE_WORKSPACE`（`_ID` サフィックスなし）を読み取ります——これは[リージョン設定](#リージョンとエンドポイントの設定)で使用する `DASHSCOPE_WORKSPACE_ID` とは別の変数です。定期実行デプロイメントの完全な例は [`samples/agentstudio_deployments.py`](samples/agentstudio_deployments.py) を参照してください。

### ローカルトークナイズ

API を呼び出さずに、ローカルで Qwen 系モデルのトークン数カウントやエンコード/デコードができます（`pip install "dashscope[tokenizer]"` が必要）：

```python
from dashscope.tokenizers.tokenizer import get_tokenizer

tokenizer = get_tokenizer("qwen-turbo")  # 任意の qwen-* モデルで利用可能
tokens = tokenizer.encode("这个是千问tokenizer")
print(len(tokens))               # トークン数
print(tokenizer.decode(tokens))  # トークンからテキストへ復元
```

### ファインチューニング

学習用ファイルをアップロードし、ファインチューニングジョブを作成して完了まで待機します（Agentic RL ファインチューニングには `pip install "dashscope[rl]"` が必要。従来の教師ありファインチューニングには追加インストール不要）：

```python
from dashscope import Files, FineTunes

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]

job = FineTunes.call(
    model="qwen-turbo",
    training_file_ids=file_id,
    hyper_parameters={"n_epochs": 10, "learning_rate": 0.001},
)
print(job.output.job_id, job.output.status)

result = FineTunes.wait(job.output.job_id)  # 完了するまで30秒ごとにポーリング
print(result.output.status)
```

カスタムの rollout/reward 関数を使う Agentic RL ファインチューニング（YAML 駆動のトレーニングジョブ、トレーシング／可観測性）については、[`dashscope/finetune/reinforcement/examples/workspace/README.md`](dashscope/finetune/reinforcement/examples/workspace/README.md)（クイックスタート、英語）と [`UserGuide.md`](dashscope/finetune/reinforcement/examples/workspace/UserGuide.md)（完全なリファレンス、英語）を参照してください。

### ファインチューニング済みモデルのデプロイ

ファインチューニングジョブで生成されたモデルをデプロイし、通常のモデルと同じように呼び出せるようにします：

```python
from dashscope import Deployments, Generation

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model

# deployment.output.status が "RUNNING" になるまでポーリングしたら、通常のモデルと同様に呼び出せます:
status = Deployments.get(deployed_model).output.status
response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
```

## CLI の使い方

すべての SDK 機能は `dashscope` サブコマンドとしても利用できます（基本パッケージと一緒にインストールされます）。Python コードを書かずにスクリプトや簡単な動作確認に使えます：

```shell
# テキスト生成
dashscope generation create -m qwen-plus -p "Who are you?"
dashscope generation create -m qwen-plus -p "海についての俳句を書いて" --stream

# 利用可能なモデルの一覧・詳細確認
dashscope models list
dashscope models get qwen-plus

# ファインチューニング用ファイルのアップロード
dashscope files upload -f ./train.jsonl -p fine_tune
```

`dashscope --help` または `dashscope <command> --help`（例：`dashscope generation --help`）を実行すると、すべてのコマンドグループ（`generation`、`ft`、`files`、`deployments`、`models`、`embeddings`、`rerank`、`tokenization`、`application`、`image-synthesis`、`video-synthesis`、`multimodal-conversation`、`transcription`、`speech-synthesis`、`rl` など）とそのオプションを確認できます。引数なしで `dashscope` を実行すると、対話型の [AI アシスタント](#ai-アシスタントdashscope-sdk-expert)が起動します。

## シェル補完

該当するコマンドを一度実行した後、シェルを再起動する（または設定ファイルを再読み込みする）だけです。

| シェル | インストールコマンド |
|-------|-----------------|
| **bash** | `dashscope --install-completion bash` |
| **zsh** | `dashscope --install-completion zsh` |
| **fish** | `dashscope --install-completion fish` |

インストールせずに補完スクリプトを確認するには:
```shell
dashscope --show-completion bash
```

## ロギング

`dashscope` を import する前に `DASHSCOPE_LOGGING_LEVEL`（`info` または `debug`）を設定しておくと、コンソールハンドラが自動的に追加されます。

```shell
export DASHSCOPE_LOGGING_LEVEL='info'
```

```python
from dashscope import Generation

# リクエストの詳細が自動的にコンソールへ出力されるようになる。例:
# 2024-01-01 12:00:00,000 - dashscope - ... - INFO - request: POST https://...
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 出力

すべての SDK 呼び出しは（ストリーミングの場合は各チャンクごとに）、次のフィールドを持つレスポンスオブジェクトを返します。

```python
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

response.request_id    # str: リクエスト ID。問い合わせの際に利用する
response.status_code   # int: HTTP ステータスコード。200 は成功を意味する
response.code          # str: 失敗時のエラーコード。成功時は空文字列
response.message       # str: 失敗時のエラーメッセージ。成功時は空文字列
response.output        # Any: リクエストの出力（呼び出す API によって形式が異なる）
response.usage         # Any: トークン/クォータの使用状況
```

## ライセンス
本プロジェクトは Apache License（Version 2.0）の下でライセンスされています。
