import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.6-luna').strip()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/resume_intelligence.db')
