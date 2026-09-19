# Advanced Audio: Voice Cloning, Pronunciation Fixes, Translation, and Hot Words

> **English** | [中文](realtime-audio_zh.md) | [日本語](realtime-audio_ja.md)

This guide covers advanced audio capabilities beyond the basic TTS/ASR examples in the [README](../../README.md#speech-synthesis-tts). All of these are real, verified SDK features with no dedicated sample script, so examples here are built directly from the source signatures and their own docstrings.

## Voice Cloning (Voice Enrollment)

`VoiceEnrollmentService` (CosyVoice v2) lets you register a custom voice from a short audio sample, then use it as a `voice=` value in `SpeechSynthesizer` calls:

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = service.create_voice(
    target_model="cosyvoice-v2",
    prefix="myvoice",  # digits/lowercase letters only, <10 chars
    url="https://example.com/voice-sample.wav",
)
print(voice_id)

# List, inspect, or remove enrolled voices
for voice in service.list_voices(prefix="myvoice"):
    print(voice)
service.delete_voice(voice_id)
```

## Pronunciation and Text Fixes

`HotFix` corrects mispronounced words or replaces text before synthesis (CosyVoice v2):

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, HotFix

hot_fix = HotFix(
    pronunciation=[{"草地": "cao3 di4"}],
    replace=[{"草地": "草弟"}],
)
synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", hot_fix=hot_fix)
```

## Real-time Speech Translation

`TranslationRecognizerRealtime` transcribes and translates streaming audio in one pass:

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

## Custom Hot Words for Speech Recognition

`AsrPhraseManager` boosts recognition accuracy for specific words (e.g. song names, jargon), then applies them via `phrase_id` on `Transcription.call`:

```python
from dashscope.audio.asr import AsrPhraseManager, Transcription

# Values are boost weights, not counts
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
