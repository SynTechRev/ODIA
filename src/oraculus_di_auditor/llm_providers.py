"""LLM provider implementations for RAG system.

This module provides abstraction layer for different LLM providers:
- OpenAI (GPT-4o-mini, etc.)
- Anthropic (Claude)
- Ollama (local models)

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, context: str, **kwargs) -> str:
        """Generate text completion given prompt and context.

        Args:
            prompt: System prompt defining the task
            context: Retrieved context from vector search
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key set, service reachable, etc.)."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (GPT-4o-mini, GPT-4, etc.)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0-2.0, lower = more deterministic)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self._client = None

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.api_key)

    def generate(self, prompt: str, context: str, **kwargs) -> str:
        """Generate response using OpenAI API.

        Args:
            prompt: System prompt
            context: Retrieved context
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated response text
        """
        if not self.is_available():
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            ) from e

        # Initialize client on first use
        if self._client is None:
            self._client = openai.OpenAI(api_key=self.api_key)

        # Build messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Context:\n{context}"},
        ]

        # Override defaults with kwargs
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", 1000)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.1,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name (default: claude-3-haiku)
            temperature: Sampling temperature
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.temperature = temperature
        self._client = None

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.api_key)

    def generate(self, prompt: str, context: str, **kwargs) -> str:
        """Generate response using Anthropic API.

        Args:
            prompt: System prompt
            context: Retrieved context
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        if not self.is_available():
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            )

        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            ) from e

        # Initialize client on first use
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)

        # Override defaults with kwargs
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", 1000)

        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=prompt,
                messages=[{"role": "user", "content": f"Context:\n{context}"}],
            )
            return message.content[0].text if message.content else ""
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider for running models locally."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str | None = None,
        temperature: float = 0.1,
    ):
        """Initialize Ollama provider.

        Args:
            model: Model name (e.g., llama3.1, mistral, etc.)
            base_url: Ollama API base URL (defaults to OLLAMA_BASE_URL or localhost)
            temperature: Sampling temperature
        """
        self.model = model
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.temperature = temperature

    def is_available(self) -> bool:
        """Check if Ollama service is reachable."""
        try:
            import requests

            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, context: str, **kwargs) -> str:
        """Generate response using local Ollama.

        Args:
            prompt: System prompt
            context: Retrieved context
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        if not self.is_available():
            raise ValueError(
                f"Ollama service not reachable at {self.base_url}. "
                "Make sure Ollama is running."
            )

        try:
            import requests
        except ImportError as e:
            raise ImportError(
                "Requests package required. Install with: pip install requests"
            ) from e

        # Override defaults with kwargs
        temperature = kwargs.get("temperature", self.temperature)

        # Build combined prompt
        full_prompt = f"{prompt}\n\nContext:\n{context}"

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise


def get_provider(provider_name: str = "openai", **kwargs) -> BaseLLMProvider:
    """Factory function to get LLM provider instance.

    Args:
        provider_name: Provider name ("openai", "anthropic", "ollama")
        **kwargs: Provider-specific initialization parameters

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider name is invalid
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. Choose from: {list(providers.keys())}"
        )

    return provider_class(**kwargs)
