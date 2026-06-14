from mangaba.core.llm.providers.constants import _HF_NATIVE_TOOL_MODELS
from mangaba.core.llm.providers.hugginface import (
    HuggingFaceLLMProvider,
    hf_model_supports_tools,
)


def test_hf_model_supports_tools_matches_native_tool_models() -> None:
    native_model = next(iter(_HF_NATIVE_TOOL_MODELS))

    assert hf_model_supports_tools(native_model) is True
    assert hf_model_supports_tools("unknown/model") is False


def test_huggingface_provider_supports_native_tools_for_current_model() -> None:
    native_model = next(iter(_HF_NATIVE_TOOL_MODELS))
    provider = object.__new__(HuggingFaceLLMProvider)
    provider.model = native_model

    assert provider._supports_native_tools() is True

    provider.model = "unknown/model"

    assert provider._supports_native_tools() is False
