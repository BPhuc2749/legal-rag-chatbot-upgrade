from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import (
    LLM_MODEL,
    TEMPERATURE,
    GOOGLE_API_KEY,
)


class LLMService:
    def __init__(self):
        self.model_name = LLM_MODEL

        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=GOOGLE_API_KEY,
            temperature=TEMPERATURE,
        )

    def generate(self, prompt):
        response = self.llm.invoke(prompt)

        content = response.content

        if isinstance(content, list):
            texts = []

            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        texts.append(
                            item.get("text", "")
                        )

            content = "\n".join(texts)


        usage = getattr(
            response,
            "usage_metadata",
            {}
        )


        return {
            "text": content,

            "model": self.model_name,

            "prompt_tokens": usage.get(
                "prompt_token_count",
                0
            ),

            "completion_tokens": usage.get(
                "candidates_token_count",
                0
            ),

            "total_tokens": usage.get(
                "total_token_count",
                0
            ),

            "raw": response,
        }