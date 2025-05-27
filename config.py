# Важные данные
from dotenv import load_dotenv
import os

load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN") 
DB_URL = os.getenv("DB_URL")
AI_TOKEN = os.getenv("AI_TOKEN")

