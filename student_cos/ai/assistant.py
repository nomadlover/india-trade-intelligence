"""
Unified Student Chief of Staff Assistant Manager.
Orchestrates chat history, provider selection, tool execution, and safety validations.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from student_cos.db import Database
from student_cos.tools import ChiefOfStaffTools
from student_cos.ai.provider import (
    BaseAIProvider,
    OfflineDeterministicProvider,
    GoogleGeminiProvider,
    OllamaProvider,
    OpenRouterProvider,
    AssistantResponse,
    get_available_providers
)


class StudentChiefOfStaff:
    """
    Personal Operating System Chief of Staff Assistant.
    """

    def __init__(self, db: Optional[Database] = None, provider_name: str = "offline"):
        self.db = db or Database()
        self.tools = ChiefOfStaffTools(self.db)
        self.providers = get_available_providers()
        self.active_provider_name = provider_name if provider_name in self.providers else "offline"
        self.conversation_history: List[Dict[str, Any]] = []

    def set_provider(self, provider_name: str) -> bool:
        if provider_name in self.providers:
            self.active_provider_name = provider_name
            return True
        return False

    def get_active_provider(self) -> BaseAIProvider:
        return self.providers.get(self.active_provider_name, self.providers["offline"])

    def process_message(self, message: str) -> AssistantResponse:
        """Process a natural language user request through the active provider."""
        provider = self.get_active_provider()
        response = provider.handle_request(message, self.tools)

        # Record history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({
            "role": "assistant",
            "content": response.text,
            "tools_called": response.tools_called,
            "provider": provider.name()
        })

        return response
