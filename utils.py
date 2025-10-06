from datetime import datetime, timedelta
from database import Session, User, Project, Task, UserTask, UserProject
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import threading
from time import sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_by_telegram_id(user_id):
    session = Session()
    try:
        return session.query(User).filter(User.user_id == user_id).first()
    finally:
        session.close()

def create_user(user_data):
    session = Session()
    try:
        user = User(**user_data)
        session.add(user)
        session.commit()
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {e}")
        return None
    finally:
        session.close()

def get_user_projects(user_id):
    session = Session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return []
        
        return session.query(Project).join(UserProject).filter(
            UserProject.user_id == user.id,
            Project.is_archived == False
        ).all()
    finally:
        session.close()

def format_task_status(status):
    status_icons = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }
    return f"{status_icons.get(status, '📝')} {status}"

def notify_admins_about_new_answer(bot, task_id, user_name, user_id):
    session = Session()
    try:
        admins = session.query(User).filter(User.role == 'admin').all()
        task = session.query(Task).filter(Task.id == task_id).first()
        
        for admin in admins:
            try:
                message = f"🎯 Новый ответ на задание!\n\n"
                message += f"📝 Задание: {task.title}\n"
                message += f"👤 Пользователь: {user_name}\n"
                message += f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Посмотреть ответ", callback_data=f"view_answer_{task_id}_{user_id}")
                ]])
                
                bot.send_message(
                    chat_id=admin.user_id,
                    text=message,
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error notifying admin {admin.user_id}: {e}")
    finally:
        session.close()

def keep_alive(webhook_url):
    """Функция для поддержания бота активным"""
    def ping():
        while True:
            try:
                response = requests.get(webhook_url)
                logger.info(f"Ping status: {response.status_code}")
                sleep(300)  # Пинг каждые 5 минут
            except Exception as e:
                logger.error(f"Ping error: {e}")
                sleep(60)
    
    thread = threading.Thread(target=ping)
    thread.daemon = True
    thread.start()