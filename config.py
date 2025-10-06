import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'kub000')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Настройки времени
TIMEZONE = 'Europe/Moscow'

# Настройки для Render.com
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8443))