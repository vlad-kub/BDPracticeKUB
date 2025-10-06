import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import get_db_session, User
import keyboards as kb
import states
import utils
import config
from admin_handlers import AdminHandlers
from message_handlers import MessageHandlers
from callback_handlers import CallbackHandlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotPractice:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.admin_handlers = AdminHandlers(self.application)
        self.message_handlers = MessageHandlers(self.application)
        self.callback_handlers = CallbackHandlers(self.application)
        
        self.setup_handlers()
    
    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("admin", self.admin_login))
        self.application.add_handler(CommandHandler("cancel", self.cancel))
        
        # ConversationHandler для админ-панели
        admin_conv = ConversationHandler(
            entry_points=[CommandHandler("admin", self.admin_login)],
            states={
                states.ADMIN_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_password)
                ],
                states.ADMIN_MENU: [
                    CallbackQueryHandler(self.admin_handlers.handle_admin_callback, pattern="^admin_")
                ],
                
                # Создание проекта
                states.CREATE_PROJECT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_project_name)
                ],
                states.CREATE_PROJECT_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_project_desc)
                ],
                states.CREATE_PROJECT_BOARD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_project_board)
                ],
                
                # Создание задания
                states.CREATE_TASK_PROJECT: [
                    CallbackQueryHandler(self.handle_task_project_selection, pattern="^select_project_task_")
                ],
                states.CREATE_TASK_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_task_title)
                ],
                states.CREATE_TASK_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_task_desc)
                ],
                states.CREATE_TASK_MEDIA: [
                    MessageHandler(filters.TEXT | filters.PHOTO, self.admin_handlers.handle_create_task_media)
                ],
                states.CREATE_TASK_TARGET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_task_target)
                ],
                states.CREATE_TASK_DEADLINE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.handle_create_task_deadline)
                ],
                
                # Управление админами
                states.ADD_ADMIN_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handlers.handle_add_admin)
                ],
                states.REMOVE_ADMIN_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handlers.handle_remove_admin)
                ],
                
                # Рассылка
                states.BROADCAST_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handlers.handle_broadcast_message)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
            }
        )
        self.application.add_handler(admin_conv)
        
        # Обработчики callback'ов для пользователей
        self.application.add_handler(CallbackQueryHandler(
            self.callback_handlers.handle_callback, 
            pattern="^(my_|project_|task_|answer_|clarify_|view_|edit_)"
        ))
        
        # Общие обработчики callback'ов
        self.application.add_handler(CallbackQueryHandler(
            self.callback_handlers.handle_callback,
            pattern="^(confirm_|cancel_)"
        ))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.message_handlers.handle_message
        ))
        
        # Обработчики медиа
        self.application.add_handler(MessageHandler(
            filters.PHOTO, 
            self.message_handlers.handle_message
        ))
        
        # Обработчик для неизвестных команд
        self.application.add_handler(MessageHandler(filters.ALL, self.unknown))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name
        }
        
        # Регистрация/обновление пользователя
        existing_user = utils.get_user_by_telegram_id(user.id)
        if not existing_user:
            utils.create_user(user_data)
            welcome_text = (
                "👋 Добро пожаловать в B&DPracticeKUB!\n\n"
                "🚀 Бизнес-практика проще, чем кажется!\n\n"
                "Выберите проект для участия или дождитесь приглашения от администратора."
            )
        else:
            welcome_text = "👋 С возвращением!"
        
        await update.message.reply_text(welcome_text, reply_markup=kb.user_main_menu())
    
    async def admin_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        if user and user.role == 'admin':
            await update.message.reply_text(
                "✅ Вы уже администратор!",
                reply_markup=kb.admin_main_menu()
            )
            return states.ADMIN_MENU
        
        await update.message.reply_text("🔐 Введите пароль для доступа к админ-панели:")
        return states.ADMIN_PASSWORD
    
    async def handle_admin_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text == config.ADMIN_PASSWORD:
            user = utils.get_user_by_telegram_id(update.effective_user.id)
            session = get_db_session()
            try:
                if user:
                    user.role = 'admin'
                else:
                    # Создаем пользователя как админа
                    user_data = {
                        'user_id': update.effective_user.id,
                        'username': update.effective_user.username,
                        'full_name': update.effective_user.full_name,
                        'role': 'admin'
                    }
                    user = User(**user_data)
                    session.add(user)
                
                session.commit()
                
                await update.message.reply_text(
                    "✅ Успешный вход в админ-панель!",
                    reply_markup=kb.admin_main_menu()
                )
                return states.ADMIN_MENU
            except Exception as e:
                session.rollback()
                logger.error(f"Error in admin login: {e}")
                await update.message.reply_text("❌ Ошибка при входе в админ-панель")
                return ConversationHandler.END
            finally:
                session.close()
        else:
            await update.message.reply_text("❌ Неверный пароль. Попробуйте снова или используйте /start")
            return ConversationHandler.END
    
    async def handle_task_project_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        project_id = int(query.data.split('_')[-1])
        return await self.admin_handlers.handle_create_task_project(update, context, project_id)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = utils.get_user_by_telegram_id(update.effective_user.id)
        
        # Очищаем состояние
        context.user_data.clear()
        
        if user and user.role == 'admin':
            await update.message.reply_text(
                "❌ Действие отменено",
                reply_markup=kb.admin_main_menu()
            )
            return states.ADMIN_MENU
        else:
            await update.message.reply_text(
                "❌ Действие отменено",
                reply_markup=kb.user_main_menu()
            )
            return ConversationHandler.END
    
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "❌ Извините, я не понимаю эту команду.\n"
            "Используйте кнопки меню для навигации."
        )

def main():
    # Создаем бота
    bot_practice = BotPractice()
    
    # Запускаем систему пингов (если есть WEBHOOK_URL)
    webhook_url = os.environ.get('WEBHOOK_URL', '')
    if webhook_url:
        utils.keep_alive(webhook_url)
        logger.info("Keep-alive system started")
    
    # Запускаем бота
    port = int(os.environ.get('PORT', 8443))
    
    if webhook_url:
        # Для production (Render.com)
        bot_practice.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{webhook_url}/{config.BOT_TOKEN}",
            drop_pending_updates=True
        )
        logger.info("Bot running in webhook mode")
    else:
        # Для локальной разработки
        bot_practice.application.run_polling(drop_pending_updates=True)
        logger.info("Bot running in polling mode")

if __name__ == '__main__':
    main()