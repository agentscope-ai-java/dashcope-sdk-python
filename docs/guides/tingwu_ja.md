# TingWu：会議・産業音声分析

> [English](tingwu.md) | [中文](tingwu_zh.md) | **日本語** | [Español](tingwu_es.md) | [한국어](tingwu_ko.md)

TingWu（听悟）は、産業点検、自動車サービス通話といった構造化された音声シナリオ向けの、ドメイン特化型音声分析モデルをカバーします。ファイル URL に対するバッチ呼び出しと、ライブ音声ソースに対するリアルタイムストリーミングセッションのどちらにも対応しています。

## バッチ呼び出し

`TingWu.call` はファイル URL とドメイン固有の入力を送信し、結果を待ちます：

```python
from dashscope.multimodal.tingwu.tingwu import TingWu

response = TingWu.call(
    model="tingwu-automotive-service-inspection",
    user_defined_input={
        "fileUrl": "http://example.com/call-recording.mp3",
        "appid": "your-app-id",
    },
)
print(response)
```

## リアルタイムストリーミング

`TingWuRealtime` は WebSocket 接続経由で音声フレームをストリーミング送信し、`TingWuRealtimeCallback` を通じて進捗を通知します：

```python
from dashscope.multimodal.tingwu.tingwu_realtime import (
    TingWuRealtime,
    TingWuRealtimeCallback,
)

class Callback(TingWuRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.can_send_audio = False

    def on_started(self, task_id: str) -> None:
        print("task started:", task_id)

    def on_speech_listen(self, result: dict):
        self.can_send_audio = True

    def on_recognize_result(self, result: dict):
        print("recognize result:", result)

    def on_ai_result(self, result: dict):
        print("ai result:", result)

    def on_stopped(self) -> None:
        self.can_send_audio = False

callback = Callback()
tingwu_realtime = TingWuRealtime(
    model="tingwu-industrial-instruction",
    audio_format="pcm",
    sample_rate=16000,
    app_id="your-app-id",
    terminology="your-terminology-id",
    callback=callback,
    max_end_silence=3000,
)
tingwu_realtime.start()
with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):
        if callback.can_send_audio:
            tingwu_realtime.send_audio_frame(chunk)
tingwu_realtime.stop()
tingwu_realtime.close()
```

`terminology` は TingWu アプリ側で設定された補正／指示セットの ID を指します。`max_end_silence`（ミリ秒単位）は、そのターンが終了したと判断するまでの無音待機時間を制御します。
