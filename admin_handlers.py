import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from database import get_db_session, User, Project, Task, UserTask, UserProject, AdminAction
import keyboards as kb
import states
from datetime import datetime, timedelta
import utils

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, application):
        self.application = application
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Основное меню админки
        if data == "admin_main":
            await self.show_admin_main_menu(query)
        elif data == "admin_projects":
            await self.show_projects_management(query)
        elif data == "admin_manage":
            await self.show_admin_management(query)
        elif data == "admin_create_task":
            await self.start_create_task(query, context)
        elif data == "admin_view_answers":
            await self.show_admin_view_answers(query)
        elif data == "admin_users":
            await self.show_user_management(query)
        elif data == "admin_broadcast":
            await self.start_broadcast(query, context)
        elif data == "admin_archive":
            await self.show_archive(query)
        elif data == "exit_admin":
            await query.edit_message_text("👋 Вы вышли из админ-панели")
            return states.ConversationHandler.END
        
        # Управление проектами
        elif data == "projects_list":
            await self.show_projects_list(query)
        elif data == "project_create":
            await self.start_create_project(query, context)
        elif data.startswith("project_detail_"):
            project_id = int(data.split('_')[2])
            await self.show_project_detail(query, project_id)
        elif data.startswith("project_users_"):
            project_id = int(data.split('_')[2])
            await self.show_project_users(query, project_id)
        elif data.startswith("project_tasks_"):
            project_id = int(data.split('_')[2])
            await self.show_project_tasks(query, project_id)
        elif data.startswith("project_archive_"):
            project_id = int(data.split('_')[2])
            await self.confirm_archive_project(query, project_id)
        elif data.startswith("project_add_board_"):
            project_id = int(data.split('_')[3])
            await self.start_add_project_board(query, context, project_id)
        
        # Управление админами
        elif data == "admin_add":
            await self.start_add_admin(query, context)
        elif data == "admin_remove":
            await self.start_remove_admin(query, context)
        elif data == "admin_list":
            await self.show_admin_list(query)
        
        # Подтверждение действий
        elif data.startswith("confirm_"):
            await self.handle_confirmation(query, data)
        elif data == "cancel_action":
            await query.edit_message_text("❌ Действие отменено", reply_markup=kb.back_button("admin_main"))
    
    async def show_admin_main_menu(self, query):
        await query.edit_message_text(
            "👨‍💼 Админ-панель B&DPracticeKUB\n\n"
            "Выберите действие:",
            reply_markup=kb.admin_main_menu()
        )
    
    async def show_projects_management(self, query):
        await query.edit_message_text(
            "📁 Управление проектами:\n\n"
            "Создавайте новые проекты, управляйте существующими и просматривайте архив",
            reply_markup=kb.projects_management_menu()
        )
    
    async def show_projects_list(self, query):
        session = get_db_session()
        try:
            projects = session.query(Project).filter(Project.is_archived == False).all()
            
            if not projects:
                await query.edit_message_text(
                    "📁 Проектов пока нет.\n\nСоздайте первый проект!",
                    reply_markup=kb.back_button("admin_projects")
                )
                return
            
            text = "📁 Активные проекты:\n\n"
            keyboard = []
            
            for project in projects:
                participants_count = session.query(UserProject).filter(UserProject.project_id == project.id).count()
                tasks_count = session.query(Task).filter(Task.project_id == project.id, Task.is_active == True).count()
                
                text += f"📂 {project.name}\n"
                text += f"   👥 Участников: {participants_count}\n"
                text += f"   📝 Заданий: {tasks_count}\n"
                text += f"   📅 Создан: {project.created_at.strftime('%d.%m.%Y')}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"📋 {project.name}", callback_data=f"project_detail_{project.id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_projects")])
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()
    
    async def show_project_detail(self, query, project_id):
        session = get_db_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                await query.edit_message_text("❌ Проект не найдено")
                return
            
            participants_count = session.query(UserProject).filter(UserProject.project_id == project.id).count()
            tasks_count = session.query(Task).filter(Task.project_id == project.id, Task.is_active == True).count()
            
            text = f"📂 Проект: {project.name}\n\n"
            text += f"📝 Описание: {project.description or 'Не указано'}\n"
            text += f"🔗 Доска: {project.board_link or 'Не указана'}\n"
            text += f"👥 Участников: {participants_count}\n"
            text += f"📝 Активных заданий: {tasks_count}\n"
            text += f"📅 Создан: {project.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            text += "Выберите действие:"
            
            await query.edit_message_text(text, reply_markup=kb.project_actions_menu(project_id))
        finally:
            session.close()
    
    async def start_create_project(self, query, context):
        context.user_data['create_project'] = {}
        await query.edit_message_text(
            "🏗 Создание нового проекта\n\n"
            "Введите название проекта:",
            reply_markup=kb.back_button("admin_projects")
        )
        return states.CREATE_PROJECT_NAME
    
    async def handle_create_project_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        project_name = update.message.text
        context.user_data['create_project']['name'] = project_name
        
        await update.message.reply_text(
            "📝 Введите описание проекта:",
            reply_markup=kb.back_button("admin_projects")
        )
        return states.CREATE_PROJECT_DESC
    
    async def handle_create_project_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        project_desc = update.message.text
        context.user_data['create_project']['description'] = project_desc
        
        await update.message.reply_text(
            "🔗 Введите ссылку на общую доску (или отправьте '-' чтобы пропустить):",
            reply_markup=kb.back_button("admin_projects")
        )
        return states.CREATE_PROJECT_BOARD
    
    async def handle_create_project_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        board_link = update.message.text
        if board_link != '-':
            context.user_data['create_project']['board_link'] = board_link
        
        # Сохраняем проект в базу
        session = get_db_session()
        try:
            admin_user = utils.get_user_by_telegram_id(update.effective_user.id)
            
            project = Project(
                name=context.user_data['create_project']['name'],
                description=context.user_data['create_project']['description'],
                board_link=context.user_data['create_project'].get('board_link'),
                created_by=admin_user.id
            )
            
            session.add(project)
            session.commit()
            
            # Логируем действие
            admin_action = AdminAction(
                admin_id=admin_user.id,
                action_type='create_project',
                target_id=project.id,
                details=f"Создан проект: {project.name}"
            )
            session.add(admin_action)
            session.commit()
            
            await update.message.reply_text(
                f"✅ Проект '{project.name}' успешно создан!",
                reply_markup=kb.admin_main_menu()
            )
            
            # Очищаем временные данные
            context.user_data.pop('create_project', None)
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await update.message.reply_text("❌ Ошибка при создании проекта")
        finally:
            session.close()
        
        return states.ConversationHandler.END
    
    async def start_create_task(self, query, context):
        session = get_db_session()
        try:
            projects = session.query(Project).filter(Project.is_archived == False).all()
            
            if not projects:
                await query.edit_message_text(
                    "❌ Нет активных проектов. Сначала создайте проект!",
                    reply_markup=kb.back_button("admin_main")
                )
                return states.ConversationHandler.END
            
            context.user_data['create_task'] = {}
            
            await query.edit_message_text(
                "📝 Создание нового задания\n\n"
                "Выберите проект:",
                reply_markup=kb.projects_list_keyboard(projects, "select_project_task")
            )
            return states.CREATE_TASK_PROJECT
        finally:
            session.close()
    
    async def handle_create_task_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id):
        context.user_data['create_task']['project_id'] = project_id
        
        await update.callback_query.edit_message_text(
            "✏️ Введите название задания:",
            reply_markup=kb.back_button("admin_main")
        )
        return states.CREATE_TASK_TITLE
    
    async def handle_create_task_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        task_title = update.message.text
        context.user_data['create_task']['title'] = task_title
        
        await update.message.reply_text(
            "📄 Введите описание задания:",
            reply_markup=kb.back_button("admin_main")
        )
        return states.CREATE_TASK_DESC
    
    async def handle_create_task_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        task_desc = update.message.text
        context.user_data['create_task']['description'] = task_desc
        
        await update.message.reply_text(
            "🖼 Отправьте фото для задания (или отправьте '-' чтобы пропустить):",
            reply_markup=kb.back_button("admin_main")
        )
        return states.CREATE_TASK_MEDIA
    
    async def handle_create_task_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Этот обработчик будет обрабатывать как текст, так и фото
        if update.message.photo:
            # Сохраняем информацию о фото
            photo = update.message.photo[-1]
            context.user_data['create_task']['image_file_id'] = photo.file_id
        elif update.message.text == '-':
            # Пропускаем добавление медиа
            pass
        
        await update.message.reply_text(
            "👥 Кому назначить задание?\n\n"
            "Отправьте 'всем' для всех участников проекта\n"
            "Или @username конкретного пользователя\n"
            "Или несколько @username через пробел",
            reply_markup=kb.back_button("admin_main")
        )
        return states.CREATE_TASK_TARGET
    
    async def handle_create_task_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        target_text = update.message.text
        context.user_data['create_task']['target'] = target_text
        
        await update.message.reply_text(
            "⏰ Установите дедлайн для задания (в формате ДД.ММ.ГГГГ ЧЧ:ММ)\n"
            "Или отправьте '-' чтобы не устанавливать дедлайн",
            reply_markup=kb.back_button("admin_main")
        )
        return states.CREATE_TASK_DEADLINE
    
    async def handle_create_task_deadline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        deadline_text = update.message.text
        
        session = get_db_session()
        try:
            # Парсим дедлайн
            deadline = None
            if deadline_text != '-':
                try:
                    deadline = datetime.strptime(deadline_text, '%d.%m.%Y %H:%M')
                except ValueError:
                    await update.message.reply_text(
                        "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ\n"
                        "Попробуйте снова:"
                    )
                    return states.CREATE_TASK_DEADLINE
            
            # Получаем данные для создания задания
            project_id = context.user_data['create_task']['project_id']
            admin_user = utils.get_user_by_telegram_id(update.effective_user.id)
            
            # Создаем задание
            task = Task(
                project_id=project_id,
                title=context.user_data['create_task']['title'],
                description=context.user_data['create_task']['description'],
                deadline=deadline,
                created_by=admin_user.id
            )
            
            # Обрабатываем целевых пользователей
            target_text = context.user_data['create_task']['target']
            target_users = []
            
            if target_text.lower() == 'всем':
                # Назначаем всем участникам проекта
                project_users = session.query(UserProject).filter(UserProject.project_id == project_id).all()
                target_users = [up.user_id for up in project_users]
            else:
                # Ищем пользователей по username
                usernames = [username.strip('@') for username in target_text.split() if username.startswith('@')]
                for username in usernames:
                    user = session.query(User).filter(User.username == username).first()
                    if user:
                        # Проверяем, что пользователь в проекте
                        user_project = session.query(UserProject).filter(
                            UserProject.user_id == user.id,
                            UserProject.project_id == project_id
                        ).first()
                        if user_project:
                            target_users.append(user.id)
            
            task.target_users = target_users
            
            # Сохраняем задание
            session.add(task)
            session.commit()
            
            # Логируем действие
            admin_action = AdminAction(
                admin_id=admin_user.id,
                action_type='create_task',
                target_id=task.id,
                details=f"Создано задание: {task.title} для проекта {task.project_id}"
            )
            session.add(admin_action)
            session.commit()
            
            # Отправляем уведомления пользователям
            await self.notify_users_about_new_task(task, target_users)
            
            await update.message.reply_text(
                f"✅ Задание '{task.title}' успешно создано и отправлено {len(target_users)} пользователям!",
                reply_markup=kb.admin_main_menu()
            )
            
            # Очищаем временные данные
            context.user_data.pop('create_task', None)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await update.message.reply_text("❌ Ошибка при создании задания")
        finally:
            session.close()
        
        return states.ConversationHandler.END
    
    async def notify_users_about_new_task(self, task, target_user_ids):
        session = get_db_session()
        try:
            for user_id in target_user_ids:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    try:
                        message = f"🎯 Новое задание!\n\n"
                        message += f"📂 Проект: {session.query(Project).filter(Project.id == task.project_id).first().name}\n"
                        message += f"📝 {task.title}\n"
                        message += f"📄 {task.description}\n"
                        if task.deadline:
                            message += f"⏰ Дедлайн: {task.deadline.strftime('%d.%m.%Y %H:%M')}\n"
                        
                        keyboard = InlineKeyboardMarkup([[
                            InlineKeyboardButton("📋 Перейти к заданию", callback_data=f"task_detail_{task.id}")
                        ]])
                        
                        await self.application.bot.send_message(
                            chat_id=user.user_id,
                            text=message,
                            reply_markup=keyboard
                        )
                    except Exception as e:
                        logger.error(f"Error notifying user {user.user_id}: {e}")
        finally:
            session.close()
    
    async def show_admin_view_answers(self, query):
        session = get_db_session()
        try:
            # Получаем задания с ответами
            tasks_with_answers = session.query(Task).join(UserTask).filter(
                UserTask.status == 'pending'
            ).distinct().all()
            
            if not tasks_with_answers:
                await query.edit_message_text(
                    "📊 Ответов для проверки пока нет.",
                    reply_markup=kb.back_button("admin_main")
                )
                return
            
            text = "📊 Ответы для проверки:\n\n"
            keyboard = []
            
            for task in tasks_with_answers:
                pending_count = session.query(UserTask).filter(
                    UserTask.task_id == task.id,
                    UserTask.status == 'pending'
                ).count()
                
                text += f"📝 {task.title}\n"
                text += f"   ⏳ Ожидает проверки: {pending_count}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"{task.title} ({pending_count})", callback_data=f"view_task_answers_{task.id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_main")])
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()

    async def show_admin_management(self, query):
        await query.edit_message_text(
            "👥 Управление администраторами:\n\n"
            "Добавление или удаление прав администратора",
            reply_markup=kb.admin_management_menu()
        )
    
    async def start_add_admin(self, query, context):
        context.user_data['state'] = 'waiting_add_admin'
        await query.edit_message_text(
            "➕ Добавление администратора\n\n"
            "Введите @username пользователя (без @):",
            reply_markup=kb.back_button("admin_manage")
        )
        return states.ADD_ADMIN_USERNAME
    
    async def start_remove_admin(self, query, context):
        context.user_data['state'] = 'waiting_remove_admin'
        await query.edit_message_text(
            "➖ Удаление администратора\n\n"
            "Введите @username пользователя (без @):",
            reply_markup=kb.back_button("admin_manage")
        )
        return states.REMOVE_ADMIN_USERNAME
    
    async def show_admin_list(self, query):
        session = get_db_session()
        try:
            admins = session.query(User).filter(User.role == 'admin').all()
            
            if not admins:
                await query.edit_message_text(
                    "📋 Администраторов пока нет.",
                    reply_markup=kb.back_button("admin_manage")
                )
                return
            
            text = "📋 Список администраторов:\n\n"
            for admin in admins:
                text += f"👤 {admin.full_name}\n"
                text += f"   @{admin.username if admin.username else 'нет username'}\n"
                text += f"   📅 С {admin.created_at.strftime('%d.%m.%Y')}\n\n"
            
            await query.edit_message_text(text, reply_markup=kb.back_button("admin_manage"))
        finally:
            session.close()
    
    async def start_broadcast(self, query, context):
        await query.edit_message_text(
            "📢 Система рассылки\n\n"
            "Выберите тип рассылки:",
            reply_markup=kb.broadcast_type_menu()
        )
    
    async def handle_broadcast_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, broadcast_type):
        context.user_data['broadcast_data'] = {'type': broadcast_type}
        context.user_data['state'] = 'waiting_broadcast_message'
        
        if broadcast_type == 'all':
            await update.callback_query.edit_message_text(
                "📢 Рассылка всем пользователям\n\n"
                "Введите сообщение для рассылки:",
                reply_markup=kb.back_button("admin_main")
            )
        elif broadcast_type == 'project':
            session = get_db_session()
            try:
                projects = session.query(Project).filter(Project.is_archived == False).all()
                await update.callback_query.edit_message_text(
                    "📁 Рассылка по проекту\n\n"
                    "Выберите проект:",
                    reply_markup=kb.projects_list_keyboard(projects, "broadcast_project")
                )
            finally:
                session.close()
            return states.BROADCAST_PROJECT
        elif broadcast_type == 'user':
            session = get_db_session()
            try:
                users = session.query(User).all()
                await update.callback_query.edit_message_text(
                    "👤 Рассылка конкретному пользователю\n\n"
                    "Выберите пользователя:",
                    reply_markup=kb.users_list_keyboard(users, "broadcast_user")
                )
            finally:
                session.close()
            return states.BROADCAST_USER
        
        return states.BROADCAST_MESSAGE
    
    async def handle_broadcast_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id):
        context.user_data['broadcast_data']['project_id'] = project_id
        await update.callback_query.edit_message_text(
            f"📁 Рассылка участникам проекта\n\n"
            f"Введите сообщение для рассылки:",
            reply_markup=kb.back_button("admin_main")
        )
        return states.BROADCAST_MESSAGE
    
    async def handle_broadcast_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
        context.user_data['broadcast_data']['user_id'] = user_id
        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            await update.callback_query.edit_message_text(
                f"👤 Рассылка пользователю: {user.full_name}\n\n"
                f"Введите сообщение для рассылки:",
                reply_markup=kb.back_button("admin_main")
            )
        finally:
            session.close()
        return states.BROADCAST_MESSAGE
    
    async def show_archive(self, query):
        session = get_db_session()
        try:
            archived_projects = session.query(Project).filter(Project.is_archived == True).all()
            
            if not archived_projects:
                await query.edit_message_text(
                    "🗄 Архив проектов пуст.",
                    reply_markup=kb.back_button("admin_main")
                )
                return
            
            text = "🗄 Архив проектов:\n\n"
            keyboard = []
            
            for project in archived_projects:
                participants_count = session.query(UserProject).filter(UserProject.project_id == project.id).count()
                text += f"📂 {project.name}\n"
                text += f"   👥 Участников: {participants_count}\n"
                text += f"   📅 Архивирован: {project.created_at.strftime('%d.%m.%Y')}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"📋 {project.name}", callback_data=f"project_detail_{project.id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_main")])
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()
    
    async def handle_confirmation(self, query, data):
        action_parts = data.split('_')
        action = action_parts[1]
        
        if action == 'archive_project':
            project_id = int(action_parts[2])
            await self.archive_project(query, project_id)
        elif action == 'delete_task':
            task_id = int(action_parts[2])
            await self.delete_task(query, task_id)
        elif action == 'approve_answer':
            user_task_id = int(action_parts[2])
            await self.approve_answer(query, user_task_id)
        elif action == 'reject_answer':
            user_task_id = int(action_parts[2])
            await self.reject_answer(query, user_task_id)
    
    async def archive_project(self, query, project_id):
        session = get_db_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                project.is_archived = True
                session.commit()
                
                await query.edit_message_text(
                    f"✅ Проект '{project.name}' перемещен в архив!",
                    reply_markup=kb.back_button("admin_projects")
                )
            else:
                await query.edit_message_text("❌ Проект не найден")
        except Exception as e:
            logger.error(f"Error archiving project: {e}")
            await query.edit_message_text("❌ Ошибка при архивации проекта")
        finally:
            session.close()
    
    async def confirm_archive_project(self, query, project_id):
        session = get_db_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                await query.edit_message_text(
                    f"🗄 Архивирование проекта\n\n"
                    f"Вы уверены, что хотите архивировать проект '{project.name}'?\n\n"
                    f"⚠️ Все задания проекта станут неактивными.",
                    reply_markup=kb.confirmation_buttons("archive_project", project_id)
                )
        finally:
            session.close()
    
    async def approve_answer(self, query, user_task_id):
        session = get_db_session()
        try:
            user_task = session.query(UserTask).filter(UserTask.id == user_task_id).first()
            if user_task:
                user_task.status = 'approved'
                user_task.reviewed_at = datetime.now()
                session.commit()
                
                # Уведомляем пользователя
                user = session.query(User).filter(User.id == user_task.user_id).first()
                task = session.query(Task).filter(Task.id == user_task.task_id).first()
                
                try:
                    await self.application.bot.send_message(
                        chat_id=user.user_id,
                        text=f"🎉 Ваш ответ на задание '{task.title}' был утвержден!"
                    )
                except Exception as e:
                    logger.error(f"Error notifying user about approval: {e}")
                
                await query.edit_message_text(
                    "✅ Ответ утвержден! Пользователь уведомлен.",
                    reply_markup=kb.back_button("admin_view_answers")
                )
            else:
                await query.edit_message_text("❌ Ответ не найден")
        except Exception as e:
            logger.error(f"Error approving answer: {e}")
            await query.edit_message_text("❌ Ошибка при утверждении ответа")
        finally:
            session.close()
    
    async def reject_answer(self, query, user_task_id):
        session = get_db_session()
        try:
            user_task = session.query(UserTask).filter(UserTask.id == user_task_id).first()
            if user_task:
                user_task.status = 'rejected'
                user_task.reviewed_at = datetime.now()
                session.commit()
                
                # Уведомляем пользователя
                user = session.query(User).filter(User.id == user_task.user_id).first()
                task = session.query(Task).filter(Task.id == user_task.task_id).first()
                
                try:
                    await self.application.bot.send_message(
                        chat_id=user.user_id,
                        text=f"❌ Ваш ответ на задание '{task.title}' был отклонен.\n\n"
                             "Пожалуйста, пересмотрите задание и отправьте ответ заново."
                    )
                except Exception as e:
                    logger.error(f"Error notifying user about rejection: {e}")
                
                await query.edit_message_text(
                    "❌ Ответ отклонен! Пользователь уведомлен.",
                    reply_markup=kb.back_button("admin_view_answers")
                )
            else:
                await query.edit_message_text("❌ Ответ не найден")
        except Exception as e:
            logger.error(f"Error rejecting answer: {e}")
            await query.edit_message_text("❌ Ошибка при отклонении ответа")
        finally:
            session.close()