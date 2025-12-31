from abc import ABC, abstractmethod


class AbstractLLMProvider(ABC):
    @abstractmethod
    def generate_response(self, text: str, category: str, urgency: str, snippets: list) -> dict:
        """
        Generates a structured response for a banking complaint.

        Args:
            text: The customer complaint xt.
            category: Detected category of the complaint.
            urgency: Detected urgency level.
            snippets: List of relevant RAG snippets.

        Returns:
            dict: Structured response containing action_plan, customer_reply_draft, etc.
        """
        pass
