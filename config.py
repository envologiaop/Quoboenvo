"""
Configuration settings for the Telegram userbot.
Handles environment variables and API credentials.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Configuration class for userbot settings."""
    
    def __init__(self):
        # Pyrogram session string (contains API credentials)
        self.SESSION_STRING = os.getenv('SESSION_STRING', '')
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required configuration is present."""
        if not self.SESSION_STRING:
            raise ValueError("SESSION_STRING environment variable is required")
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        try:
            self._validate_config()
            return True
        except ValueError:
            return False
