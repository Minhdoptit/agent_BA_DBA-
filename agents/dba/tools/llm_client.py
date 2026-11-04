"""LLM Client for Google Gemini API.

Provides a unified interface for querying Google Gemini models with graceful
offline fallback handling and structured response extraction.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("dba_agent.llm_client")


class GeminiClient:
    """Wrapper around Google Generative AI (Gemini) SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("LLM_API_KEY")
            or ""
        )
        self.model_name = (
            model_name
            or os.getenv("GEMINI_MODEL")
            or os.getenv("LLM_MODEL")
            or "gemini-2.5-flash"
        )
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(temperature)))
        self._model = None
        self._initialized = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Google Generative AI client if API key is provided."""
        if not self.api_key:
            logger.info("No Gemini API key detected; running in deterministic fallback mode.")
            self._initialized = False
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": self.temperature},
            )
            self._initialized = True
            logger.info("GeminiClient initialized successfully with model: %s", self.model_name)
        except Exception as exc:
            logger.warning("Failed to initialize Google Gemini client: %s", exc)
            self._initialized = False

    @property
    def is_available(self) -> bool:
        """Check if Gemini client is active and configured."""
        return self._initialized and self._model is not None

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> Optional[str]:
        """Send prompt to Gemini model and return text response.

        Returns None if client is unavailable or if call fails.
        """
        if not self.is_available:
            return None

        try:
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_instruction}\n\nUSER REQUEST:\n{prompt}"

            response = self._model.generate_content(full_prompt)
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return None
        except Exception as exc:
            logger.error("Gemini generation failed: %s", exc)
            return None
