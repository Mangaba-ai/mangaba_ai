import os
from typing import Dict

from dotenv import load_dotenv

# Carrega automaticamente o .env
load_dotenv()


class Config:
    """Configuração centralizada e agnóstica de provedor para Mangaba."""

    SUPPORTED_PROVIDERS = ("google", "openai", "anthropic", "huggingface")
    DEFAULT_MODELS: Dict[str, str] = {
        "google": "gemini-2.5-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "huggingface": "mistralai/Mistral-7B-Instruct-v0.2",
    }

    def __init__(self) -> None:
        provider = (
            os.getenv("LLM_PROVIDER")
            or os.getenv("AI_PROVIDER")
            or os.getenv("PROVIDER")
            or "google"
        ).lower()

        provider = provider.replace("_", "-")
        alias_normalization = {
            "gemini": "google",
            "google-ai": "google",
            "googleai": "google",
            "gpt": "openai",
            "chatgpt": "openai",
            "claude": "anthropic",
            "hf": "huggingface",
            "hugging-face": "huggingface",
        }
        self.provider = alias_normalization.get(provider, provider)

        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"[ERROR] Provedor '{self.provider}' não suportado. "
                f"Use um dos: {', '.join(self.SUPPORTED_PROVIDERS)}"
            )

        self.model = (
            os.getenv("MODEL_NAME")
            or os.getenv("MODEL")
            or self.DEFAULT_MODELS.get(self.provider)
            or "gemini-2.5-flash"
        )

        # API Keys específicas por provedor
        self.api_keys: Dict[str, str] = {
            "google": os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "huggingface": os.getenv("HUGGINGFACE_API_KEY")
            or os.getenv("HUGGINGFACE_TOKEN")
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        }

        fallback_api_key = os.getenv("API_KEY")
        self.api_key = self.api_keys.get(self.provider) or fallback_api_key

        if not self.api_key:
            raise ValueError(
                f"[ERROR] API key para o provedor '{self.provider}' não encontrada! "
                "Configure no arquivo .env (ex: GOOGLE_API_KEY, OPENAI_API_KEY, etc.)"
            )

        # Hiperparâmetros padrão
        self.temperature = float(
            os.getenv("MODEL_TEMPERATURE", os.getenv("TEMPERATURE", 0.7))
        )
        self.max_output_tokens = int(
            os.getenv("MAX_OUTPUT_TOKENS", os.getenv("MAX_TOKENS", 1024))
        )
        self.system_prompt = os.getenv("SYSTEM_PROMPT")

        # Opcionais gerais
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def __str__(self) -> str:
        return (
            f"Config(provider={self.provider}, model={self.model}, "
            f"log_level={self.log_level})"
        )


# Instância global para facilitar
config = Config()
