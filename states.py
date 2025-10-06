from telegram.ext import ConversationHandler

# Состояния для админ-панели
ADMIN_PASSWORD, ADMIN_MENU = range(2)

# Состояния для создания задания
CREATE_TASK_PROJECT, CREATE_TASK_TITLE, CREATE_TASK_DESC, CREATE_TASK_MEDIA, CREATE_TASK_TARGET, CREATE_TASK_DEADLINE = range(2, 8)

# Состояния для управления проектами
CREATE_PROJECT_NAME, CREATE_PROJECT_DESC, CREATE_PROJECT_BOARD = range(8, 11)

# Состояния для управления пользователями
ADD_USER_USERNAME, REMOVE_USER_USERNAME, EDIT_USER_ROLE = range(11, 14)

# Состояния для рассылки
BROADCAST_TYPE, BROADCAST_MESSAGE, BROADCAST_PROJECT, BROADCAST_USER = range(14, 18)

# Состояния для ответов пользователя
ANSWER_TASK, SUPPLEMENT_ANSWER, CLARIFY_TASK = range(18, 21)

# Состояния для обратной связи
FEEDBACK_MESSAGE = 21

# Состояния для редактирования профиля
EDIT_PROFILE_NAME, EDIT_PROFILE_STATUS = range(22, 24)

# Состояния для управления админами
ADD_ADMIN_USERNAME, REMOVE_ADMIN_USERNAME = range(24, 26)

# Состояния для добавления доски проекта
ADD_PROJECT_BOARD = 26

# Состояния для редактирования задания
EDIT_TASK_TITLE, EDIT_TASK_DESC, EDIT_TASK_MEDIA, EDIT_TASK_DEADLINE = range(27, 31)