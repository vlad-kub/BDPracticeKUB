import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session, User, Task, UserTask, Project
import keyboards as kb
import states
import utils
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageHandlers:
    def __init__(self, application):
        self.application = application
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_state = context.user_data.get('state')
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
            return
        
        # Обработка состояний пользователя
        if user_state == 'waiting_task_answer':
            await self.handle_task_answer_text(update, context)
        elif user_state == 'waiting_task_answer_media':
            await self.handle_task_answer_media(update, context)
        elif user_state == 'waiting_clarification':
            await self.handle_clarification(update, context)
        elif user_state == 'waiting_feedback':
            await self.handle_feedback(update, context)
        elif user_state == 'waiting_broadcast_message':
            await self.handle_broadcast_message(update, context)
        elif user_state == 'waiting_edit_name':
            await self.handle_edit_name(update, context)
        elif user_state == 'waiting_edit_status':
            await self.handle_edit_status(update, context)
        elif user_state == 'waiting_add_admin':
            await self.handle_add_admin(update, context)
        elif user_state == 'waiting_remove_admin':
            await self.handle_remove_admin(update, context)
        elif user_state == 'waiting_add_user':
            await self.handle_add_user(update, context)
        elif user_state == 'waiting_remove_user':
            await self.handle_remove_user(update, context)
        else:
            # Общее сообщение
            if user.role == 'admin':
                await update.message.reply_text(
                    "👨‍💼 Используйте админ-панель для управления ботом",
                    reply_markup=kb.admin_main_menu()
                )
            else:
                await update.message.reply_text(
                    "🏠 Используйте кнопки меню для навигации",
                    reply_markup=kb.user_main_menu()
                )
    
    async def handle_task_answer_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        task_id = context.user_data.get('current_task_id')
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            # Проверяем, есть ли уже ответ
            existing_answer = session.query(UserTask).filter(
                UserTask.user_id == user.id,
                UserTask.task_id == task_id
            ).first()
            
            if existing_answer:
                # Обновляем существующий ответ
                existing_answer.answer_text = update.message.text
                existing_answer.submitted_at = datetime.now()
                existing_answer.status = 'pending'
                existing_answer.feedback = None  # Сбрасываем фидбек при изменении
            else:
                # Создаем новый ответ
                user_task = UserTask(
                    user_id=user.id,
                    task_id=task_id,
                    answer_text=update.message.text,
                    submitted_at=datetime.now(),
                    status='pending'
                )
                session.add(user_task)
            
            session.commit()
            
            # Уведомляем админов
            task = session.query(Task).filter(Task.id == task_id).first()
            project = session.query(Project).filter(Project.id == task.project_id).first()
            
            admins = session.query(User).filter(User.role == 'admin').all()
            for admin in admins:
                try:
                    message = f"🎯 Новый ответ на задание!\n\n"
                    message += f"📂 Проект: {project.name}\n"
                    message += f"📝 Задание: {task.title}\n"
                    message += f"👤 Пользователь: {user.full_name} (@{user.username})\n"
                    message += f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    
                    keyboard = [
                        [InlineKeyboardButton("📋 Посмотреть ответ", callback_data=f"view_answer_{user_task.id}")]
                    ]
                    
                    await self.application.bot.send_message(
                        chat_id=admin.user_id,
                        text=message,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin.user_id}: {e}")
            
            await update.message.reply_text(
                "✅ Ваш ответ успешно отправлен на проверку!\n"
                "Ожидайте обратной связи от администратора.",
                reply_markup=kb.back_button("my_tasks")
            )
            
            # Сбрасываем состояние
            context.user_data['state'] = None
            context.user_data['current_task_id'] = None
            
        except Exception as e:
            logger.error(f"Error saving task answer: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении ответа")
        finally:
            session.close()
    
    async def handle_task_answer_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Обработка медиа в ответах (будет реализована позже)
        await update.message.reply_text("📸 Фото получено! Теперь добавьте текстовый комментарий.")
    
    async def handle_clarification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        task_id = context.user_data.get('clarify_task_id')
        question = update.message.text
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            # Отправляем вопрос админам
            admins = session.query(User).filter(User.role == 'admin').all()
            for admin in admins:
                try:
                    message = f"❓ Вопрос по заданию!\n\n"
                    message += f"📂 Проект: {session.query(Project).filter(Project.id == task.project_id).first().name}\n"
                    message += f"📝 Задание: {task.title}\n"
                    message += f"👤 Пользователь: {user.full_name} (@{user.username})\n"
                    message += f"❓ Вопрос: {question}\n"
                    message += f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    
                    keyboard = [
                        [InlineKeyboardButton("💬 Ответить", callback_data=f"answer_clarification_{user.id}_{task_id}")]
                    ]
                    
                    await self.application.bot.send_message(
                        chat_id=admin.user_id,
                        text=message,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    logger.error(f"Error sending clarification to admin {admin.user_id}: {e}")
            
            await update.message.reply_text(
                "✅ Ваш вопрос отправлен администраторам. Ожидайте ответа.",
                reply_markup=kb.back_button("my_tasks")
            )
            
            # Сбрасываем состояние
            context.user_data['state'] = None
            context.user_data['clarify_task_id'] = None
            
        except Exception as e:
            logger.error(f"Error handling clarification: {e}")
            await update.message.reply_text("❌ Ошибка при отправке вопроса")
        finally:
            session.close()
    
    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_task_id = context.user_data.get('feedback_user_task_id')
        feedback_text = update.message.text
        
        session = get_db_session()
        try:
            user_task = session.query(UserTask).filter(UserTask.id == user_task_id).first()
            if user_task:
                user_task.feedback = feedback_text
                user_task.status = 'rejected'
                user_task.reviewed_at = datetime.now()
                
                session.commit()
                
                # Уведомляем пользователя
                user = session.query(User).filter(User.id == user_task.user_id).first()
                task = session.query(Task).filter(Task.id == user_task.task_id).first()
                
                try:
                    message = f"💬 Получена обратная связь!\n\n"
                    message += f"📝 Задание: {task.title}\n"
                    message += f"💬 Комментарий: {feedback_text}\n\n"
                    message += "🔄 Пожалуйста, переделайте задание с учетом комментариев."
                    
                    await self.application.bot.send_message(
                        chat_id=user.user_id,
                        text=message,
                        reply_markup=kb.back_button("my_tasks")
                    )
                except Exception as e:
                    logger.error(f"Error notifying user about feedback: {e}")
                
                await update.message.reply_text(
                    "✅ Обратная связь отправлена пользователю!",
                    reply_markup=kb.admin_main_menu()
                )
            
            # Сбрасываем состояние
            context.user_data['state'] = None
            context.user_data['feedback_user_task_id'] = None
            
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            await update.message.reply_text("❌ Ошибка при отправке обратной связи")
        finally:
            session.close()
    
    async def handle_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        broadcast_data = context.user_data.get('broadcast_data', {})
        message_text = update.message.text
        
        session = get_db_session()
        try:
            # Определяем целевых пользователей
            users_to_notify = []
            
            if broadcast_data['type'] == 'all':
                users_to_notify = session.query(User).all()
            elif broadcast_data['type'] == 'project':
                project_users = session.query(UserProject).filter(
                    UserProject.project_id == broadcast_data['project_id']
                ).all()
                user_ids = [up.user_id for up in project_users]
                users_to_notify = session.query(User).filter(User.id.in_(user_ids)).all()
            elif broadcast_data['type'] == 'user':
                user = session.query(User).filter(User.id == broadcast_data['user_id']).first()
                if user:
                    users_to_notify = [user]
            
            # Отправляем сообщения
            success_count = 0
            for user in users_to_notify:
                try:
                    await self.application.bot.send_message(
                        chat_id=user.user_id,
                        text=message_text
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending broadcast to user {user.user_id}: {e}")
            
            await update.message.reply_text(
                f"✅ Рассылка отправлена {success_count}/{len(users_to_notify)} пользователям!",
                reply_markup=kb.admin_main_menu()
            )
            
            # Очищаем временные данные
            context.user_data.pop('broadcast_data', None)
            context.user_data['state'] = None
            
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            await update.message.reply_text("❌ Ошибка при отправке рассылки")
        finally:
            session.close()
    
    async def handle_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_name = update.message.text
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            user.full_name = new_name
            session.commit()
            
            await update.message.reply_text(
                "✅ Имя успешно изменено!",
                reply_markup=kb.user_main_menu()
            )
            context.user_data['state'] = None
        except Exception as e:
            logger.error(f"Error updating name: {e}")
            await update.message.reply_text("❌ Ошибка при изменении имени")
        finally:
            session.close()
    
    async def handle_edit_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_status = update.message.text
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            user.status = new_status
            session.commit()
            
            await update.message.reply_text(
                "✅ Статус успешно изменен!",
                reply_markup=kb.user_main_menu()
            )
            context.user_data['state'] = None
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            await update.message.reply_text("❌ Ошибка при изменении статуса")
        finally:
            session.close()
    
    async def handle_add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip('@')
        current_admin = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            # Ищем пользователя
            user = session.query(User).filter(User.username == username).first()
            if not user:
                await update.message.reply_text(
                    f"❌ Пользователь @{username} не найден.\n"
                    "Пользователь должен сначала запустить бота через /start",
                    reply_markup=kb.back_button("admin_manage")
                )
                return
            
            # Делаем пользователя админом
            user.role = 'admin'
            session.commit()
            
            # Логируем действие
            from database import AdminAction
            admin_action = AdminAction(
                admin_id=current_admin.id,
                action_type='add_admin',
                target_id=user.id,
                details=f"Добавлен администратор: {user.full_name} (@{user.username})"
            )
            session.add(admin_action)
            session.commit()
            
            # Уведомляем нового админа
            try:
                await self.application.bot.send_message(
                    chat_id=user.user_id,
                    text="🎉 Вам были предоставлены права администратора!\n\n"
                         "Используйте команду /admin для доступа к админ-панели."
                )
            except Exception as e:
                logger.error(f"Error notifying new admin: {e}")
            
            await update.message.reply_text(
                f"✅ Пользователь @{username} теперь администратор!",
                reply_markup=kb.admin_main_menu()
            )
            
            context.user_data['state'] = None
            
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            await update.message.reply_text("❌ Ошибка при добавлении администратора")
        finally:
            session.close()
    
    async def handle_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip('@')
        current_admin = utils.get_user_by_telegram_id(update.effective_user.id)
        
        session = get_db_session()
        try:
            # Ищем пользователя
            user = session.query(User).filter(User.username == username).first()
            if not user:
                await update.message.reply_text(
                    f"❌ Пользователь @{username} не найден.",
                    reply_markup=kb.back_button("admin_manage")
                )
                return
            
            if user.id == current_admin.id:
                await update.message.reply_text(
                    "❌ Вы не можете удалить сами себя!",
                    reply_markup=kb.back_button("admin_manage")
                )
                return
            
            # Убираем права админа
            user.role = 'user'
            session.commit()
            
            # Логируем действие
            from database import AdminAction
            admin_action = AdminAction(
                admin_id=current_admin.id,
                action_type='remove_admin',
                target_id=user.id,
                details=f"Удален администратор: {user.full_name} (@{user.username})"
            )
            session.add(admin_action)
            session.commit()
            
            # Уведомляем бывшего админа
            try:
                await self.application.bot.send_message(
                    chat_id=user.user_id,
                    text="ℹ️ Ваши права администратора были отозваны."
                )
            except Exception as e:
                logger.error(f"Error notifying removed admin: {e}")
            
            await update.message.reply_text(
                f"✅ Пользователь @{username} больше не администратор!",
                reply_markup=kb.admin_main_menu()
            )
            
            context.user_data['state'] = None
            
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            await update.message.reply_text("❌ Ошибка при удалении администратора")
        finally:
            session.close()