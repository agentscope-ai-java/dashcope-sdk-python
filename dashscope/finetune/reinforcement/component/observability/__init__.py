"""OpenTelemetry integration for AgenticRL function components."""

from dashscope.finetune.reinforcement.component.observability.genai import (
    dashscope_response_to_output_messages,
    genai_llm_span,
    instrument_dashscope_generation_call,
    instrument_openai_chat_completions,
    observe_llm,
    observe_tool,
    openai_chat_messages_to_input_messages,
    openai_completion_to_output_messages,
    run_with_genai_llm_span,
    trace_client,
    trace_tool,
)
from dashscope.finetune.reinforcement.component.observability.processor_span import (
    observe_processor,
    trace_processor_span,
)
from dashscope.finetune.reinforcement.component.observability.tracing import (
    AGENTIC_RL_ATTEMPT_ID_BAGGAGE_KEY,
    AGENTIC_RL_ROLLOUT_ID_BAGGAGE_KEY,
    AGENTIC_RL_SAMPLE_ID_BAGGAGE_KEY,
    apply_processor_span_attributes_after,
    apply_processor_span_attributes_before,
    async_trace_processor_process,
    current_trace_id_hex,
    ensure_agentic_rl_baggage_span_processor,
    get_tracer,
    is_tracing_enabled,
    log_trace_id,
    resolve_processor_func_type_for_span,
    rollout_context,
    span_payload_preview,
    trace_processor_process,
)

__all__ = [
    # public API
    "observe_llm",
    "observe_processor",
    "observe_tool",
    "rollout_context",
    "trace_client",
    "trace_tool",
    # utility functions / low-level interfaces
    "AGENTIC_RL_ATTEMPT_ID_BAGGAGE_KEY",
    "AGENTIC_RL_ROLLOUT_ID_BAGGAGE_KEY",
    "AGENTIC_RL_SAMPLE_ID_BAGGAGE_KEY",
    "apply_processor_span_attributes_after",
    "apply_processor_span_attributes_before",
    "current_trace_id_hex",
    "ensure_agentic_rl_baggage_span_processor",
    "dashscope_response_to_output_messages",
    "genai_llm_span",
    "get_tracer",
    "instrument_dashscope_generation_call",
    "instrument_openai_chat_completions",
    "is_tracing_enabled",
    "log_trace_id",
    "openai_chat_messages_to_input_messages",
    "openai_completion_to_output_messages",
    "run_with_genai_llm_span",
    "resolve_processor_func_type_for_span",
    "span_payload_preview",
    "trace_processor_process",
    "async_trace_processor_process",
    "trace_processor_span",
]
