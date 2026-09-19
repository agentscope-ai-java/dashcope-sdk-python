# Audio Avanzado: Clonación de Voz, Corrección de Pronunciación, Traducción y Palabras Clave

> [English](realtime-audio.md) | [中文](realtime-audio_zh.md) | [日本語](realtime-audio_ja.md) | **Español** | [한국어](realtime-audio_ko.md)

Esta guía cubre capacidades de audio avanzadas más allá de los ejemplos básicos de TTS/ASR del [README](../../README.md#speech-synthesis-tts). Todas estas son funciones reales y verificadas del SDK sin un script de ejemplo dedicado, por lo que los ejemplos aquí se construyen directamente a partir de las firmas del código fuente y sus propios docstrings.

## Clonación de Voz (Voice Enrollment)

`VoiceEnrollmentService` (CosyVoice v2) le permite registrar una voz personalizada a partir de una muestra de audio corta, y luego usarla como valor de `voice=` en llamadas a `SpeechSynthesizer`:

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = service.create_voice(
    target_model="cosyvoice-v2",
    prefix="myvoice",  # solo dígitos/letras minúsculas, <10 caracteres
    url="https://example.com/voice-sample.wav",
)
print(voice_id)

# Listar, inspeccionar o eliminar voces registradas
for voice in service.list_voices(prefix="myvoice"):
    print(voice)
service.delete_voice(voice_id)
```

## Correcciones de Pronunciación y Texto

`HotFix` corrige palabras mal pronunciadas o reemplaza texto antes de la síntesis (CosyVoice v2):

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, HotFix

hot_fix = HotFix(
    pronunciation=[{"草地": "cao3 di4"}],
    replace=[{"草地": "草弟"}],
)
synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", hot_fix=hot_fix)
```

## Traducción de Voz en Tiempo Real

`TranslationRecognizerRealtime` transcribe y traduce audio en streaming en un solo paso:

```python
from dashscope.audio.asr import TranslationRecognizerCallback, TranslationRecognizerRealtime

class Callback(TranslationRecognizerCallback):
    def on_event(self, request_id, transcription_result, translation_result, usage) -> None:
        if transcription_result is not None and transcription_result.is_sentence_end:
            print("transcript:", transcription_result.text)
        if translation_result is not None:
            translation = translation_result.get_translation("en")
            if translation.is_sentence_end:
                print("translation:", translation.text)

translator = TranslationRecognizerRealtime(
    model="gummy-realtime-v1",
    format="pcm",
    sample_rate=16000,
    transcription_enabled=True,
    translation_enabled=True,
    translation_target_languages=["en"],
    callback=Callback(),
)
translator.start()
with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):
        translator.send_audio_frame(chunk)
translator.stop()
```

## Palabras Clave Personalizadas para el Reconocimiento de Voz

`AsrPhraseManager` mejora la precisión de reconocimiento para palabras específicas (p. ej. nombres de canciones, jerga), que luego se aplican mediante `phrase_id` en `Transcription.call`:

```python
from dashscope.audio.asr import AsrPhraseManager, Transcription

# Los valores son pesos de refuerzo, no conteos
job = AsrPhraseManager.create_phrases(
    model="paraformer-v1",
    phrases={"下一首": 90, "上一首": 90},
)
phrase_id = job.output.job_id

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
    phrase_id=phrase_id,
)
```
