import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.SESSION_STRING = os.getenv('SESSION_STRING', '')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '') # <--- ADD THIS LINE
        
        self._validate_config()
    
    def _validate_config(self):
        if not self.SESSION_STRING:
            raise ValueError("SESSION_STRING environment variable is required")
        # You might want to add validation for GEMINI_API_KEY as well
        # if not self.GEMINI_API_KEY:
        #     raise ValueError("GEMINI_API_KEY environment variable is required for AI features")

    @property
    def is_valid(self) -> bool:
        try:
            self._validate_config()
            return True
        except ValueError:
            return False
