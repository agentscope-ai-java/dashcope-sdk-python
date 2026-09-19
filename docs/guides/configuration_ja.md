# 高度な設定

> [English](configuration.md) | [中文](configuration_zh.md) | **日本語**

このガイドでは、認証とリージョン選択以外の SDK 全体の設定について説明します。API Key の設定については [API Key 認証](../../README.md#api-key-authentication) を、リージョン／エンドポイントの切り替えについては [リージョンとエンドポイントの設定](../../README.md#region-and-endpoint-configuration) を参照してください。

## リクエストタイムアウト

`.call()`/`.create()`/`.get()`/`.list()`/`.delete()` 系のすべてのメソッドは
`request_timeout` キーワード引数（秒単位）を受け付けます。デフォルト値は
300 秒（`DEFAULT_REQUEST_TIMEOUT_SECONDS`）です。ストリーミングリクエストの
場合はチャンク間のアイドルタイムアウトとして、非ストリーミングリクエストの
場合はリクエスト全体のタイムアウトとして扱われます。

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    request_timeout=30,
)
```

## カスタムリクエストヘッダー

`headers` 辞書を渡すことで、追加の HTTP ヘッダーをリクエストにマージできます
（SDK 自身の `Authorization`／ワークスペース用ヘッダーはそのまま適用されます）：

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    headers={"X-Request-Tag": "my-service"},
)
```

OpenAI 互換の `Completions.create` には、同じ目的専用の `extra_headers`
パラメータが用意されています：

```python
from dashscope.aigc.chat_completion import Completions

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hi"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    extra_headers={"X-Request-Tag": "my-service"},
)
```

## プロキシのサポート

SDK 自体は独自のプロキシ設定を実装していません。代わりに、内部で使用している
HTTP ライブラリの標準的な挙動に依存しています。非同期クライアントは
`trust_env=True` を指定して `aiohttp.ClientSession` を作成し、同期クライアントの
`requests.Session` もデフォルトでプロキシに対応しています——どちらも標準の
`HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY` 環境変数を自動的に読み取ります：

```shell
export HTTPS_PROXY="http://proxy.example.com:8080"
```

```python
from dashscope import Generation

# リクエストは HTTPS_PROXY で設定したプロキシ経由で送信されます
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 共有コネクションプールのクローズ

SDK は、コネクションプーリングのために共有の `requests.Session`（同期）と、
イベントループごとの `aiohttp.ClientSession`（非同期）を維持しています。
長時間実行されるプロセスでは、プールされた接続を解放するためにこれらを
明示的にクローズできます（次回のリクエスト時に新しいセッションが遅延生成されます）：

```python
import asyncio
from dashscope import close_shared_sync_session, close_shared_aio_session

close_shared_sync_session()
asyncio.run(close_shared_aio_session())
```

## ロギング

[README](../../README.md#logging) で説明されているとおり、インポート前に
`DASHSCOPE_LOGGING_LEVEL` を設定すると、コンソールへのログハンドラーが
自動的に付加されます。SDK は標準の `logging` モジュールを通じて
`"dashscope"` という logger 名でログを出力しているため、環境変数を使わずに
プログラムから直接ログレベルを制御することもできます：

```python
import logging

logging.getLogger("dashscope").setLevel(logging.DEBUG)
```
