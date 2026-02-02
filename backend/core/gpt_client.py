"""
GPT API client for generating feedback.

Handles OpenAI API interactions including prompt formatting, response generation,
and JSON extraction from model responses.
"""

import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class GPTClient:
    """Client for interacting with OpenAI's GPT models."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize GPT client.

        Args:
            model: OpenAI model name (default: gpt-4o-mini).
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def query_gpt(self, conversation_history: list) -> str:
        """
        Query GPT model with conversation history and return response.

        Args:
            conversation_history: List of message dicts with 'role' and 'content'.

        Returns:
            str: Model response text.
        """
        def to_chat_message(msg):
            if isinstance(msg["content"], list):
                return {"role": msg["role"], "content": msg["content"]}
            else:
                return {
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}],
                }

        formatted_messages = [to_chat_message(m) for m in conversation_history]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        model_response = response.choices[0].message.content
        if model_response is not None:
            model_response = model_response.strip()
        else:
            model_response = ""

        return model_response

    @staticmethod
    def extract_json(response_text: str) -> dict:
        """
        Extract JSON object from GPT response text.

        Uses regex to find the first JSON object (delimited by curly braces)
        within the response text.

        Args:
            response_text: Text containing JSON object.

        Returns:
            dict: Extracted JSON object.

        Raises:
            ValueError: If no JSON object found or decoding fails.
        """
        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
                return json.loads(json_content)
            else:
                raise ValueError("No JSON object found in the response.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")
