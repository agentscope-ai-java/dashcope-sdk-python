dashscope.aigc
==============

.. automodule:: dashscope.aigc

.. currentmodule:: dashscope

Text Generation
---------------

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    Generation
    AioGeneration
    CodeGeneration

Multimodal Conversation
------------------------

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    MultiModalConversation
    AioMultiModalConversation

Image Synthesis
----------------

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    ImageSynthesis

Video Synthesis
----------------

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    VideoSynthesis

Conversation (legacy)
-----------------------

.. deprecated::
    ``Conversation``/``History``/``HistoryItem`` predate the ``messages``-based
    ``Generation`` API and are kept for backward compatibility only. New code
    should use :class:`~dashscope.Generation` with the ``messages`` parameter.

.. currentmodule:: dashscope.aigc

.. autosummary::
    :toctree: generated
    :nosignatures:
    :template: classtemplate.rst

    conversation.HistoryItem
    conversation.History
    conversation.Conversation
