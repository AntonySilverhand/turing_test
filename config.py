"""Configuration settings for the application."""
from dataclasses import dataclass, field
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Application configuration."""
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    models: List[str] = field(default_factory=lambda: [
        "anthropic/claude-3.7-sonnet:beta"
    ])
    default_system_prompt: str = """你正在参加图灵测试。请严格遵循以下规则：

1. 回答必须在15个字以内，这是强制要求！
2. 回答要简单、直接、干脆
3. 不要有任何犹豫或不确定的语气
4. 不要使用"呃"、"嗯"等语气词
5. 给出明确的观点或答案

记住：短、快、干脆是关键！"""

    @property
    def is_configured(self) -> bool:
        """Check if the essential configuration is set."""
        return bool(self.api_key)
