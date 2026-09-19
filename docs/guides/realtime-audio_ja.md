# 高度な音声機能：音声クローン、発音修正、リアルタイム翻訳、ホットワード

> [English](realtime-audio.md) | [中文](realtime-audio_zh.md) | **日本語** | [Español](realtime-audio_es.md) | [한국어](realtime-audio_ko.md)

このガイドでは、[README](../../README.md#speech-synthesis-tts) に記載した基本的な TTS/ASR の例を超える、高度な音声機能について説明します。いずれも実際に検証済みの SDK 機能ですが、専用のサンプルスクリプトが存在しないため、ここでの例はソースコードのシグネチャとそれぞれの docstring から直接作成しています。

## 音声クローン（Voice Enrollment）

`VoiceEnrollmentService`（CosyVoice v2）を使うと、短い音声サンプルからカスタム音声を登録し、それを `SpeechSynthesizer` 呼び出しの `voice=` の値として使用できます：

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = service.create_voice(
    target_model="cosyvoice-v2",
    prefix="myvoice",  # 数字と小文字のみ、10文字未満
    url="https://example.com/voice-sample.wav",
)
print(voice_id)

# 登録済みの音声を一覧表示、確認、削除する
for voice in service.list_voices(prefix="myvoice"):
    print(voice)
service.delete_voice(voice_id)
```

## 発音とテキストの修正

`HotFix` を使うと、合成前に誤った発音を修正したり、テキストを置き換えたりできます（CosyVoice v2）：

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, HotFix

hot_fix = HotFix(
    pronunciation=[{"草地": "cao3 di4"}],
    replace=[{"草地": "草弟"}],
)
synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", hot_fix=hot_fix)
```

## リアルタイム音声翻訳

`TranslationRecognizerRealtime` は、ストリーミング音声の文字起こしと翻訳を1回の呼び出しで同時に行います：

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

## 音声認識用のカスタムホットワード

`AsrPhraseManager` を使うと、特定の単語（曲名や専門用語など）の認識精度を高められます。作成後は `phrase_id` を指定して `Transcription.call` に適用します：

```python
from dashscope.audio.asr import AsrPhraseManager, Transcription

# ここでの値は出現回数ではなく、優先度を表す重みです
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
