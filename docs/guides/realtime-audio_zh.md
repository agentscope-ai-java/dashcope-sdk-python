# 高级语音功能：音色复刻、发音纠正、实时翻译与热词

> [English](realtime-audio.md) | **中文** | [日本語](realtime-audio_ja.md) | [Español](realtime-audio_es.md) | [한국어](realtime-audio_ko.md)

本指南介绍 [README](../../README.md#speech-synthesis-tts) 中基础 TTS/ASR 示例之外的高级语音能力。以下均为真实、已验证的 SDK 功能，但没有专门的示例脚本，因此本文示例均直接基于源码签名及其自带的 docstring 编写。

## 音色复刻（Voice Enrollment）

`VoiceEnrollmentService`（CosyVoice v2）可以从一段简短的音频样本注册一个自定义音色，随后即可将其作为 `SpeechSynthesizer` 调用中的 `voice=` 值使用：

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = service.create_voice(
    target_model="cosyvoice-v2",
    prefix="myvoice",  # 仅限数字和小写字母，长度小于 10 个字符
    url="https://example.com/voice-sample.wav",
)
print(voice_id)

# 列出、查看或删除已注册的音色
for voice in service.list_voices(prefix="myvoice"):
    print(voice)
service.delete_voice(voice_id)
```

## 发音与文本纠正

`HotFix` 可以在合成之前纠正读错的字词或替换文本（CosyVoice v2）：

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, HotFix

hot_fix = HotFix(
    pronunciation=[{"草地": "cao3 di4"}],
    replace=[{"草地": "草弟"}],
)
synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", hot_fix=hot_fix)
```

## 实时语音翻译

`TranslationRecognizerRealtime` 可以在一次调用中同时完成流式音频的转写与翻译：

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

## 语音识别自定义热词

`AsrPhraseManager` 可以提升特定词汇（例如歌曲名、专业术语）的识别准确率，创建后通过 `phrase_id` 参数应用到 `Transcription.call`：

```python
from dashscope.audio.asr import AsrPhraseManager, Transcription

# 这里的数值是热词权重，而不是出现次数
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
