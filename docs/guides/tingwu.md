# TingWu: Meeting and Industrial Audio Analysis

> **English** | [中文](tingwu_zh.md) | [日本語](tingwu_ja.md) | [Español](tingwu_es.md) | [한국어](tingwu_ko.md)

TingWu (听悟) covers domain-specific audio analysis models — industrial inspections, automotive service calls, and similar structured-audio scenarios — as a batch call over a file URL, or a real-time streaming session over a live audio source.

## Batch Call

`TingWu.call` submits a file URL and domain-specific input, and waits for the result:

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

## Real-time Streaming

`TingWuRealtime` streams audio frames over a WebSocket connection and reports progress through a `TingWuRealtimeCallback`:

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

`terminology` references a correction/instruction set id configured on the TingWu app; `max_end_silence` (in milliseconds) controls how long to wait in silence before the task considers a turn finished.
