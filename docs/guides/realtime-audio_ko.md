# 고급 오디오: 음성 복제, 발음 수정, 번역, 핫워드

> [English](realtime-audio.md) | [中文](realtime-audio_zh.md) | [日本語](realtime-audio_ja.md) | [Español](realtime-audio_es.md) | **한국어**

이 가이드는 [README](../../README.md#speech-synthesis-tts)의 기본 TTS/ASR
예제를 넘어서는 고급 오디오 기능을 다룹니다. 이 기능들은 모두 실제로 검증된
SDK 기능이지만 전용 예제 스크립트가 없으므로, 여기 예제는 소스 시그니처와
자체 docstring을 바탕으로 직접 작성되었습니다.

## 음성 복제 (Voice Enrollment)

`VoiceEnrollmentService`(CosyVoice v2)를 사용하면 짧은 오디오 샘플로부터
커스텀 음성을 등록한 뒤, 이를 `SpeechSynthesizer` 호출의 `voice=` 값으로
사용할 수 있습니다:

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = service.create_voice(
    target_model="cosyvoice-v2",
    prefix="myvoice",  # 숫자/소문자만, 10자 미만
    url="https://example.com/voice-sample.wav",
)
print(voice_id)

# 등록된 음성 목록 조회, 확인, 삭제
for voice in service.list_voices(prefix="myvoice"):
    print(voice)
service.delete_voice(voice_id)
```

## 발음 및 텍스트 수정

`HotFix`는 합성 전에 잘못 발음되는 단어를 수정하거나 텍스트를 치환합니다
(CosyVoice v2):

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, HotFix

hot_fix = HotFix(
    pronunciation=[{"草地": "cao3 di4"}],
    replace=[{"草地": "草弟"}],
)
synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", hot_fix=hot_fix)
```

## 실시간 음성 번역

`TranslationRecognizerRealtime`은 스트리밍 오디오를 한 번에 전사하고
번역합니다:

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

## 음성 인식을 위한 커스텀 핫워드

`AsrPhraseManager`는 특정 단어(예: 노래 제목, 전문 용어)에 대한 인식 정확도를
높여주며, `Transcription.call`에서 `phrase_id`로 적용합니다:

```python
from dashscope.audio.asr import AsrPhraseManager, Transcription

# 값은 개수가 아니라 가중치입니다
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
