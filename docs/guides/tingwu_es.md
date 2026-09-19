# TingWu: análisis de audio de reuniones e industrial

> [English](tingwu.md) | [中文](tingwu_zh.md) | [日本語](tingwu_ja.md) | **Español** | [한국어](tingwu_ko.md)

TingWu (听悟) cubre modelos de análisis de audio específicos de dominio — inspecciones industriales, llamadas de servicio automotriz y escenarios de audio estructurado similares — como una llamada por lotes sobre una URL de archivo, o una sesión de streaming en tiempo real sobre una fuente de audio en vivo.

## Llamada por lotes

`TingWu.call` envía una URL de archivo y una entrada específica del dominio, y espera el resultado:

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

## Streaming en tiempo real

`TingWuRealtime` transmite frames de audio a través de una conexión WebSocket y reporta el progreso mediante un `TingWuRealtimeCallback`:

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

`terminology` hace referencia a un id de conjunto de correcciones/instrucciones configurado en la app de TingWu; `max_end_silence` (en milisegundos) controla cuánto tiempo de silencio se espera antes de considerar finalizado un turno.
