# エラーハンドリングリファレンス

> [English](error-handling.md) | [中文](error-handling_zh.md) | **日本語**

これは [README のエラーハンドリングの節](../../README.md#error-handling)
（`DashScopeException` を捕捉し、`status_code` を確認する基本パターン）を
さらに掘り下げた内容です。

## 例外クラス

SDK が送出するすべての例外（`dashscope/common/error.py`）は
`DashScopeException` を継承しているため、`except DashScopeException` 一つで
そのいずれも捕捉できます。よく使われるものと、実際にどのような場合に
送出されるかは次のとおりです：

| 例外 | 発生する場合 |
|---|---|
| `InputRequired` | 必須の入力が欠けている場合、例：`prompt`/`messages` が指定されていない |
| `ModelRequired` | `model` 引数が空の場合 |
| `AuthenticationError` | API Key がどこにも（コード、環境変数、ファイル）設定されていない場合 |
| `InvalidInput` | 引数の組み合わせが不正な場合、例：矛盾するパラメータの指定 |
| `InvalidFileFormat` | アップロードするファイルが想定フォーマットと一致しない場合（例：ファインチューニング用ファイルが JSONL 形式でない） |
| `UnsupportedModel` | その操作でリクエストされたモデルがサポートされていない場合（例：ローカルトークナイズが対応していないモデル） |
| `UploadFileException` | ローカルファイル（例：ビジョン／画像リクエスト用）の OSS へのアップロードに失敗した場合 |
| `UnsupportedDataType` | 入力／出力のデータ型が認識できない場合 |
| `TimeoutException` | ブロッキングの待機処理（例：`Runs.wait`）がタイムアウトを超えた場合 |

```python
from dashscope import Generation
from dashscope.common.error import (
    DashScopeException,
    InputRequired,
    ModelRequired,
    AuthenticationError,
)

try:
    Generation.call(model="", messages=[{"role": "user", "content": "Hi"}])
except ModelRequired as e:
    print(f"Model missing: {e}")
except (InputRequired, AuthenticationError) as e:
    print(f"Invalid setup: {e}")
except DashScopeException as e:
    print(f"Other SDK-side error: {e}")
```

## サポート問い合わせ用の request_id の取得

成功・失敗を問わず、すべてのレスポンスには `request_id` が含まれます。
問題を報告したりサポートに問い合わせたりする際は、これを添えてください：

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
if response.status_code != HTTPStatus.OK:
    print(f"request_id={response.request_id} code={response.code} message={response.message}")
```

## 自動的なコネクション再試行

プールされていたキープアライブ接続がサーバーや途中のロードバランサーによって
静かに切断されていた場合（レスポンスのバイトが1つも届く前に接続エラーとして
検知された場合）、SDK はそのリクエストを内部で**一度だけ**自動的に
再試行します——同期（`requests` ベース）・非同期（`aiohttp` ベース）の
どちらのクライアントもこれを内部で行います。この挙動は設定変更できず、
利用者側のコードも不要です。あくまで「レスポンスが開始する前に接続が
切断された」場合のみをカバーするものであり、レート制限や不正な入力といった
アプリケーションレベルの失敗（README のエラーハンドリングの節で説明した
パターンで、通常のエラーレスポンスとして返されます）は対象外です。
