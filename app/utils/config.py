import os
from dotenv import load_dotenv

# Load from home directory ~/.env first, then override with local project root .env
home_env = os.path.expanduser("~/.env")
if os.path.exists(home_env):
    load_dotenv(home_env)
load_dotenv()  # Load from local directory .env

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            # Check standard fallback environment variables
            cls.GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
            
        # We need GEMINI_API_KEY to run the model
        if not cls.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY is not set in environment variables or .env file.")
