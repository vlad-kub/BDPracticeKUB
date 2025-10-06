from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Главное меню админа
def admin_main_menu():
    keyboard = [
        [InlineKeyboardButton("👥 Управление админами", callback_data="admin_manage")],
        [InlineKeyboardButton("📁 Управление проектами", callback_data="admin_projects")],
        [InlineKeyboardButton("📝 Дать задание", callback_data="admin_create_task")],
        [InlineKeyboardButton("📊 Посмотреть ответы", callback_data="admin_view_answers")],
        [InlineKeyboardButton("👤 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Рассылка/обратная связь", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🗄 Архив проектов", callback_data="admin_archive")],
        [InlineKeyboardButton("🔙 Выйти из админки", callback_data="exit_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню управления проектами
def projects_management_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Список проектов", callback_data="projects_list")],
        [InlineKeyboardButton("➕ Создать проект", callback_data="project_create")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню действий с проектом
def project_actions_menu(project_id):
    keyboard = [
        [InlineKeyboardButton("👥 Участники", callback_data=f"project_users_{project_id}")],
        [InlineKeyboardButton("📝 Задания", callback_data=f"project_tasks_{project_id}")],
        [InlineKeyboardButton("🔗 Добавить доску", callback_data=f"project_add_board_{project_id}")],
        [InlineKeyboardButton("✏️ Изменить", callback_data=f"project_edit_{project_id}")],
        [InlineKeyboardButton("🗄 Архивировать", callback_data=f"project_archive_{project_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_projects")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню пользователя
def user_main_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Мои задания", callback_data="my_tasks")],
        [InlineKeyboardButton("📤 Мои ответы", callback_data="my_answers")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton("📊 Общая доска", callback_data="common_board")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Кнопка назад
def back_button(back_to):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=back_to)]])

# Подтверждение действий
def confirmation_buttons(action, data=""):
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню управления админами
def admin_management_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton("➖ Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton("📋 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню для ответов на задания
def task_answer_menu(task_id, has_answer=False):
    if has_answer:
        keyboard = [
            [InlineKeyboardButton("✏️ Изменить ответ", callback_data=f"answer_task_{task_id}")],
            [InlineKeyboardButton("📝 Дополнить", callback_data=f"supplement_answer_{task_id}")],
            [InlineKeyboardButton("🗑️ Удалить ответ", callback_data=f"delete_answer_{task_id}")],
            [InlineKeyboardButton("❓ Уточнить задание", callback_data=f"clarify_task_{task_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="my_tasks")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📝 Ответить", callback_data=f"answer_task_{task_id}")],
            [InlineKeyboardButton("❓ Уточнить задание", callback_data=f"clarify_task_{task_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="my_tasks")]
        ]
    return InlineKeyboardMarkup(keyboard)

# Меню модерации ответа
def answer_moderation_menu(user_task_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Утвердить", callback_data=f"approve_answer_{user_task_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_answer_{user_task_id}")
        ],
        [InlineKeyboardButton("💬 Дать обратную связь", callback_data=f"feedback_answer_{user_task_id}")],
        [InlineKeyboardButton("📋 История ответов", callback_data=f"answer_history_{user_task_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_view_answers")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню выбора проекта
def projects_list_keyboard(projects, action_prefix):
    keyboard = []
    for project in projects:
        keyboard.append([InlineKeyboardButton(project.name, callback_data=f"{action_prefix}_{project.id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(keyboard)

# Меню выбора пользователей
def users_list_keyboard(users, action_prefix):
    keyboard = []
    for user in users:
        keyboard.append([InlineKeyboardButton(f"{user.full_name} (@{user.username})", callback_data=f"{action_prefix}_{user.id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)

# Меню выбора типа рассылки
def broadcast_type_menu():
    keyboard = [
        [InlineKeyboardButton("📢 Всем пользователям", callback_data="broadcast_all")],
        [InlineKeyboardButton("📁 По проекту", callback_data="broadcast_project")],
        [InlineKeyboardButton("👤 Конкретному пользователю", callback_data="broadcast_user")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню редактирования профиля
def profile_edit_menu():
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_name")],
        [InlineKeyboardButton("🎯 Изменить статус", callback_data="edit_status")],
        [InlineKeyboardButton("🔙 Назад", callback_data="user_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню управления заданиями
def task_management_menu(task_id):
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить задание", callback_data=f"edit_task_{task_id}")],
        [InlineKeyboardButton("🗑️ Удалить задание", callback_data=f"delete_task_{task_id}")],
        [InlineKeyboardButton("📊 Посмотреть ответы", callback_data=f"view_task_answers_{task_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_view_answers")]
    ]
    return InlineKeyboardMarkup(keyboard)