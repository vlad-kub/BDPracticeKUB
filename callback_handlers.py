import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db_session, User, Project, Task, UserTask, UserProject
import keyboards as kb
import states
import utils
from datetime import datetime

logger = logging.getLogger(__name__)

class CallbackHandlers:
    def __init__(self, application):
        self.application = application
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = utils.get_user_by_telegram_id(query.from_user.id)
        
        if not user:
            await query.edit_message_text("❌ Пользователь не найден")
            return
        
        # Определяем тип callback и перенаправляем обработку
        if data.startswith('admin_'):
            await self.handle_admin_callback(query, context, data, user)
        elif data.startswith('project_'):
            await self.handle_project_callback(query, context, data, user)
        elif data.startswith('task_'):
            await self.handle_task_callback(query, context, data, user)
        elif data.startswith('user_'):
            await self.handle_user_callback(query, context, data, user)
        elif data.startswith('confirm_'):
            await self.handle_confirmation(query, context, data, user)
        elif data.startswith('answer_'):
            await self.handle_answer_callback(query, context, data, user)
        elif data.startswith('my_'):
            await self.handle_my_callback(query, context, data, user)
        else:
            await query.edit_message_text("❌ Неизвестная команда")
    
    async def handle_my_callback(self, query, context, data, user):
        """Обработка callback'ов пользовательского меню"""
        if data == "my_tasks":
            await self.show_user_tasks(query, user)
        elif data == "my_answers":
            await self.show_user_answers(query, user)
        elif data == "my_profile":
            await self.show_user_profile(query, user)
        elif data == "common_board":
            await self.show_common_board(query)
        elif data == "edit_name":
            await self.start_edit_name(query, context)
        elif data == "edit_status":
            await self.start_edit_status(query, context)
    
    async def show_user_tasks(self, query, user):
        session = get_db_session()
        try:
            # Получаем проекты пользователя
            user_projects = session.query(UserProject).filter(UserProject.user_id == user.id).all()
            if not user_projects:
                await query.edit_message_text(
                    "📋 У вас пока нет заданий.\n\n"
                    "Вы не участвуете в проектах или для вас еще не создали задания.",
                    reply_markup=kb.back_button("user_main")
                )
                return
            
            project_ids = [up.project_id for up in user_projects]
            
            # Получаем активные задания из проектов пользователя
            tasks = session.query(Task).filter(
                Task.project_id.in_(project_ids),
                Task.is_active == True
            ).all()
            
            if not tasks:
                await query.edit_message_text(
                    "📋 Заданий пока нет.\n\n"
                    "Ожидайте, когда администратор создаст задания для ваших проектов.",
                    reply_markup=kb.back_button("user_main")
                )
                return
            
            text = "📋 Мои задания:\n\n"
            keyboard = []
            
            for task in tasks:
                user_task = session.query(UserTask).filter(
                    UserTask.user_id == user.id,
                    UserTask.task_id == task.id
                ).first()
                
                status_icon = "🆕" if not user_task else utils.format_task_status(user_task.status)
                deadline_text = f"⏰ До {task.deadline.strftime('%d.%m.%Y %H:%M')}" if task.deadline else ""
                project = session.query(Project).filter(Project.id == task.project_id).first()
                
                text += f"{status_icon} {task.title}\n"
                text += f"   📂 {project.name}\n"
                text += f"   {deadline_text}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{task.title} {status_icon}", 
                        callback_data=f"task_detail_{task.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="user_main")])
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()
    
    async def show_user_answers(self, query, user):
        session = get_db_session()
        try:
            user_tasks = session.query(UserTask).filter(
                UserTask.user_id == user.id
            ).join(Task).all()
            
            if not user_tasks:
                await query.edit_message_text(
                    "📤 У вас пока нет отправленных ответов.",
                    reply_markup=kb.back_button("user_main")
                )
                return
            
            text = "📤 Мои ответы:\n\n"
            keyboard = []
            
            for user_task in user_tasks:
                task = user_task.task
                project = session.query(Project).filter(Project.id == task.project_id).first()
                status_icon = utils.format_task_status(user_task.status)
                
                text += f"{status_icon} {task.title}\n"
                text += f"   📂 {project.name}\n"
                text += f"   📅 {user_task.submitted_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{task.title} {status_icon}", 
                        callback_data=f"view_my_answer_{user_task.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="user_main")])
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()
    
    async def show_user_profile(self, query, user):
        session = get_db_session()
        try:
            projects_count = session.query(UserProject).filter(UserProject.user_id == user.id).count()
            tasks_count = session.query(UserTask).filter(UserTask.user_id == user.id).count()
            approved_count = session.query(UserTask).filter(
                UserTask.user_id == user.id,
                UserTask.status == 'approved'
            ).count()
            
            text = f"👤 Ваш профиль:\n\n"
            text += f"🆔 ID: {user.user_id}\n"
            text += f"📛 Имя: {user.full_name}\n"
            text += f"👤 Юзернейм: @{user.username if user.username else 'не указан'}\n"
            text += f"🎯 Роль: {user.role}\n"
            text += f"📛 Статус: {user.status}\n"
            text += f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            text += f"📊 Статистика:\n"
            text += f"   📁 Проектов: {projects_count}\n"
            text += f"   📝 Ответов: {tasks_count}\n"
            text += f"   ✅ Принято: {approved_count}\n"
            
            await query.edit_message_text(text, reply_markup=kb.profile_edit_menu())
        finally:
            session.close()
    
    async def start_edit_name(self, query, context):
        context.user_data['state'] = 'waiting_edit_name'
        await query.edit_message_text(
            "✏️ Введите новое имя:",
            reply_markup=kb.back_button("my_profile")
        )
    
    async def start_edit_status(self, query, context):
        context.user_data['state'] = 'waiting_edit_status'
        await query.edit_message_text(
            "🎯 Введите новый статус:",
            reply_markup=kb.back_button("my_profile")
        )
    
    async def show_common_board(self, query):
        session = get_db_session()
        try:
            projects = session.query(Project).filter(
                Project.is_archived == False
            ).all()
            
            text = "📊 Общая доска проектов:\n\n"
            
            for project in projects:
                participants_count = session.query(UserProject).filter(UserProject.project_id == project.id).count()
                active_tasks = session.query(Task).filter(
                    Task.project_id == project.id,
                    Task.is_active == True
                ).count()
                
                text += f"📂 {project.name}\n"
                text += f"   👥 Участников: {participants_count}\n"
                text += f"   📝 Активных заданий: {active_tasks}\n"
                if project.board_link:
                    text += f"   🔗 Доска: {project.board_link}\n"
                text += "\n"
            
            await query.edit_message_text(
                text,
                reply_markup=kb.back_button("user_main")
            )
        finally:
            session.close()
    
    async def handle_task_callback(self, query, context, data, user):
        """Обработка callback'ов связанных с заданиями"""
        if data.startswith("task_detail_"):
            task_id = int(data.split('_')[2])
            await self.show_task_detail(query, task_id, user)
        elif data.startswith("answer_task_"):
            task_id = int(data.split('_')[2])
            await self.start_task_answer(query, context, task_id)
        elif data.startswith("clarify_task_"):
            task_id = int(data.split('_')[2])
            await self.start_clarify_task(query, context, task_id)
        elif data.startswith("view_my_answer_"):
            user_task_id = int(data.split('_')[3])
            await self.show_my_answer_detail(query, user_task_id)
    
    async def show_task_detail(self, query, task_id, user):
        session = get_db_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                await query.edit_message_text("❌ Задание не найдено")
                return
            
            project = session.query(Project).filter(Project.id == task.project_id).first()
            user_task = session.query(UserTask).filter(
                UserTask.user_id == user.id,
                UserTask.task_id == task_id
            ).first()
            
            text = f"📝 {task.title}\n"
            text += f"📂 Проект: {project.name}\n\n"
            text += f"📄 {task.description}\n\n"
            
            if task.deadline:
                text += f"⏰ Дедлайн: {task.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            if user_task:
                text += f"📤 Ваш ответ: {user_task.answer_text}\n"
                if user_task.feedback:
                    text += f"💬 Обратная связь: {user_task.feedback}\n"
                text += f"🎯 Статус: {utils.format_task_status(user_task.status)}\n"
                if user_task.reviewed_at:
                    text += f"📅 Проверено: {user_task.reviewed_at.strftime('%d.%m.%Y %H:%M')}\n"
            else:
                text += "❌ Вы еще не отправили ответ на это задание.\n"
            
            has_answer = user_task is not None
            await query.edit_message_text(text, reply_markup=kb.task_answer_menu(task_id, has_answer))
        finally:
            session.close()
    
    async def start_task_answer(self, query, context, task_id):
        context.user_data['current_task_id'] = task_id
        context.user_data['state'] = 'waiting_task_answer'
        
        session = get_db_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                await query.edit_message_text(
                    f"📝 Ответ на задание: {task.title}\n\n"
                    f"📄 Описание: {task.description}\n\n"
                    "💬 Напишите ваш ответ текстом:",
                    reply_markup=kb.back_button(f"task_detail_{task_id}")
                )
        finally:
            session.close()
    
    async def start_clarify_task(self, query, context, task_id):
        context.user_data['clarify_task_id'] = task_id
        context.user_data['state'] = 'waiting_clarification'
        
        await query.edit_message_text(
            "❓ Введите ваш вопрос по заданию:",
            reply_markup=kb.back_button(f"task_detail_{task_id}")
        )
    
    async def show_my_answer_detail(self, query, user_task_id):
        session = get_db_session()
        try:
            user_task = session.query(UserTask).filter(UserTask.id == user_task_id).first()
            if not user_task:
                await query.edit_message_text("❌ Ответ не найден")
                return
            
            task = user_task.task
            project = session.query(Project).filter(Project.id == task.project_id).first()
            
            text = f"📝 {task.title}\n"
            text += f"📂 Проект: {project.name}\n\n"
            text += f"📤 Ваш ответ: {user_task.answer_text}\n\n"
            text += f"🎯 Статус: {utils.format_task_status(user_task.status)}\n"
            if user_task.feedback:
                text += f"💬 Обратная связь: {user_task.feedback}\n"
            text += f"📅 Отправлен: {user_task.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
            if user_task.reviewed_at:
                text += f"📅 Проверено: {user_task.reviewed_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            keyboard = [
                [InlineKeyboardButton("✏️ Изменить ответ", callback_data=f"answer_task_{task.id}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="my_answers")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()