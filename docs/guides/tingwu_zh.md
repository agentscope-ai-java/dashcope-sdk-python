# 听悟（TingWu）：会议与工业音频分析

> [English](tingwu.md) | **中文** | [日本語](tingwu_ja.md) | [Español](tingwu_es.md) | [한국어](tingwu_ko.md)

听悟（TingWu）覆盖特定领域的音频分析模型——工业质检、汽车服务通话等结构化音频场景——既可以针对文件 URL 进行批量调用，也可以针对实时音频源建立流式会话。

## 批量调用

`TingWu.call` 提交文件 URL 与领域相关的输入内容，并等待返回结果：

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

## 实时流式处理

`TingWuRealtime` 通过 WebSocket 连接流式发送音频帧，并通过 `TingWuRealtimeCallback` 上报进度：

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

`terminology` 指向在听悟应用中配置的纠正/指令集 ID；`max_end_silence`（单位为毫秒）用于控制在判定一轮对话结束前，静音等待的时长。
