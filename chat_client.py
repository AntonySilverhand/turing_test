"""OpenRouter chat completion client implementation."""
from typing import Optional
from openai import OpenAI
from config import Config
import random
import requests
import logging

class ChatClient:
    """Client for handling chat completions."""
    
    def __init__(self, config: Config):
        """Initialize the chat client.
        
        Args:
            config: Application configuration
        """
        if not config.is_configured:
            raise ValueError("API key not configured. Please set OPENROUTER_API_KEY environment variable.")
        
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self.current_model = config.models[0]  # Default to first model
        
    def set_model(self, model: str):
        """Set the current model to use."""
        if model not in self.config.models:
            raise ValueError(f"Model {model} not in configured models: {self.config.models}")
        self.current_model = model

    def get_completion(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.9  # Higher temperature for more random/human-like responses
    ) -> str:
        """Get a chat completion response.
        
        Args:
            question: The user's question
            system_prompt: Optional system prompt (uses default if not provided)
            temperature: Controls randomness in the response (0.0-1.0)
            
        Returns:
            The assistant's response
            
        Raises:
            Exception: If the API call fails
        """
        if not system_prompt:
            system_prompt = self.config.default_system_prompt
            
        # Add quirky or uncertain behavior 20% of the time
        if random.random() < 0.2:
            extra_prompts = [
                "回答必须在15字以内！",
                "回答要简单直接，不要犹豫！",
                "给出明确的观点，不要模棱两可。"
            ]
            system_prompt = system_prompt + "\n" + random.choice(extra_prompts)

        try:
            # Each call is independent with no context from previous calls
            completion = self.client.chat.completions.create(
                model=self.current_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                stream=False,
                temperature=temperature,
                max_tokens=1000
            )
            return completion.choices[0].message.content
        except Exception as e:
            logging.error(f"API调用失败: {str(e)}")
            return f"抱歉，我遇到了一些问题: {str(e)}"
