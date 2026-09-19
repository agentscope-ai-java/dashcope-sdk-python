# TingWu: 회의 및 산업용 오디오 분석

> [English](tingwu.md) | [中文](tingwu_zh.md) | [日本語](tingwu_ja.md) | [Español](tingwu_es.md) | **한국어**

TingWu（听悟）는 산업 점검, 자동차 서비스 통화 등 구조화된 오디오 시나리오를 위한 도메인 특화 오디오 분석 모델을 다룹니다. 파일 URL에 대한 배치 호출과, 실시간 오디오 소스에 대한 실시간 스트리밍 세션을 모두 지원합니다.

## 배치 호출

`TingWu.call`은 파일 URL과 도메인별 입력을 전송하고 결과를 기다립니다:

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

## 실시간 스트리밍

`TingWuRealtime`은 WebSocket 연결을 통해 오디오 프레임을 스트리밍하고, `TingWuRealtimeCallback`을 통해 진행 상황을 보고합니다:

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

`terminology`는 TingWu 앱에 설정된 교정/지시 세트 ID를 가리킵니다. `max_end_silence`（밀리초 단위）는 한 턴이 끝났다고 판단하기 전까지 대기할 무음 시간을 제어합니다.
