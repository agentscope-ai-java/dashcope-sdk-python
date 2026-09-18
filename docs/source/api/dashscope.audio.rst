dashscope.audio
=================

.. automodule:: dashscope.audio

Speech Synthesis (Text-to-Speech)
------------------------------------

.. currentmodule:: dashscope

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    SpeechSynthesizer
    HttpSpeechSynthesizer

.. currentmodule:: dashscope.audio

CosyVoice v2 (streaming, WebSocket) and Qwen-TTS have their own dedicated
clients, in addition to the ``qwen3-tts-*`` models reachable through
:class:`~dashscope.MultiModalConversation` (see the README for a snippet):

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    tts_v2.SpeechSynthesizer
    qwen_tts.SpeechSynthesizer
    qwen_tts_realtime.QwenTtsRealtime

Speech Recognition (ASR)
--------------------------

.. currentmodule:: dashscope

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    Transcription

.. currentmodule:: dashscope.audio

Real-time recognition and speech translation (WebSocket-based) live under
``dashscope.audio.asr``:

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    asr.recognition.Recognition
    asr.translation_recognizer.TranslationRecognizerRealtime
    asr.translation_recognizer.TranslationRecognizerChat

Real-time Omni (speech-in, speech-out)
-----------------------------------------

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    qwen_omni.omni_realtime.OmniRealtimeConversation
