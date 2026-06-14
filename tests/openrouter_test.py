#######################
# Teste usando o pytest
#######################
from unittest.mock import MagicMock
from mangaba.core.types import OpenRouterConfig
from mangaba.core.llm.client import OpenRouterLLMProvider


def test_open_router_models_list():
    """Garante que a config do OpenRouter aceita lista de modelos."""
    # Arrange
    models = ["google/gemini-2.5-flash", "anthropic/claude-3.5-sonnet"]
    # Act
    cfg = OpenRouterConfig(model=models, api_key="sk-or-test")
    # Assert
    assert cfg.model == models


def test_get_call_params_formatting():
    """
    Testa se o método interno converte a lista para string
    e popula o extra_body corretamente.
    """
    # Arrange
    models = ["model-primary", "model-fallback"]
    provider = OpenRouterLLMProvider(api_key="fake-key", model=models)
    initial_kwargs = {"temperature": 0.2}

    # Act
    params = provider._get_call_params(**initial_kwargs)

    # Assert
    assert params["model"] == "model-primary"
    assert params["extra_body"]["models"] == models
    assert params["temperature"] == 0.2


def test_generate_calls_openai_sdk_correctly(mocker):
    """Garante que o SDK da OpenAI recebe o dicionário de parâmetros formatado."""
    # Arrange
    # mock
    mock_openai = mocker.patch("openai.OpenAI")
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "Vulnerabilidade encontrada"
    mock_resp.usage.prompt_tokens = 10
    mock_resp.usage.completion_tokens = 5
    mock_resp.usage.total_tokens = 15

    mock_openai.return_value.chat.completions.create.return_value = mock_resp

    provider = OpenRouterLLMProvider(api_key="key", model=["m1", "m2"])

    # Act
    provider.generate("Analise este código Rust")

    # Assert
    # Capturamos os argumentos da chamada do create
    _, kwargs = mock_openai.return_value.chat.completions.create.call_args

    assert kwargs["model"] == "m1"
    assert kwargs["extra_body"]["models"] == ["m1", "m2"]
