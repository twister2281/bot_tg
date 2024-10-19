from babel.dates import format_date
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import locale

# Установка локали на русский язык
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

# Состояния для команды /add, /edit и /get_homework
MONTH_SELECTION, DAY_INPUT, SUBJECT_SELECTION, TASK_INPUT, MONTH_REQUEST, DAY_REQUEST, EDIT_MONTH_SELECTION, EDIT_DAY_INPUT, EDIT_SUBJECT_SELECTION, EDIT_TASK_INPUT = range(10)

# Словарь для хранения домашних заданий по месяцам
homework = {}

# Определение статусов пользователей
ADMIN = 'Блатной'
USER = 'Не блатной'

# Получение текущего месяца и года
def get_current_month_year():
    now = datetime.now()
    return now

# Инициализация месячной структуры
def init_month(month_year):
    if month_year not in homework:
        homework[month_year] = {}

# Команда /start для приветствия
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_status = context.user_data.get('status', USER)  # Получаем статус пользователя
    await update.message.reply_text(
        f"Привет! Я бот для добавления и редактирования домашнего задания. "
        f"Ты в статусе: {user_status}. Используй команды /add, /edit, чтобы добавлять или редактировать задания, "
        "или /all, чтобы посмотреть все задания, или /get_homework, чтобы получить задание за конкретный день."
    )

# Установка статуса пользователя
async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['status'] = ADMIN  # Устанавливаем статус как админ для теста
    await update.message.reply_text("Статус установлен на админ.")

# Выбор месяца для добавления домашнего задания
async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_status = context.user_data.get('status', USER)  # Получаем статус пользователя
    if user_status != ADMIN:
        await update.message.reply_text("У вас нет прав для добавления домашних заданий.")
        return ConversationHandler.END
    
    current_date = get_current_month_year()
    current_month_year = current_date.strftime('%B %Y')
    months_keyboard = [
        ['Предыдущий месяц'],
        [current_month_year],
        ['Следующий месяц'],
        ['Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(months_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выбери месяц:", reply_markup=reply_markup)
    return MONTH_SELECTION
# Обработка выбора месяца для добавления домашнего задания
async def month_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_month = update.message.text
    current_date = get_current_month_year()

    if selected_month == 'Назад':
        await start(update, context)
        return ConversationHandler.END

    month_year = current_date.strftime('%B %Y')  # Инициализация переменной month_year

    if selected_month == 'Следующий месяц':
        next_month_date = current_date + timedelta(days=31)
        month_year = next_month_date.strftime('%B %Y')
    elif selected_month == 'Предыдущий месяц':
        prev_month_date = current_date - timedelta(days=31)
        month_year = prev_month_date.strftime('%B %Y')

    context.user_data['month'] = month_year
    init_month(month_year)  # Инициализация месяца, если еще не был создан

    await update.message.reply_text(f"Выбран месяц: {month_year}. Введи день (1-31):")
    return DAY_INPUT

# Обработка ввода дня
async def day_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text

    if day == 'Назад':
        await select_month(update, context)
        return MONTH_SELECTION
    
    if not day.isdigit() or int(day) < 1 or int(day) > 31:
        await update.message.reply_text("Ошибка: введите корректный день (от 1 до 31).")
        return DAY_INPUT

    context.user_data['day'] = day

    subjects_keyboard = [['Алгебра', 'Дискретная математика'],
                         ['Математический анализ', 'Русский язык'],
                         ['ОРГ', 'История России'],
                         ['Информатика', 'Физическая культура'],
                         ['Назад']]
    reply_markup = ReplyKeyboardMarkup(subjects_keyboard, one_time_keyboard=True)
    await update.message.reply_text(f"День {day} выбран. Теперь выбери предмет:", reply_markup=reply_markup)
    return SUBJECT_SELECTION

# Обработка выбора предмета
async def subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text.capitalize()

    if subject == 'Назад':
        await day_input(update, context)
        return DAY_INPUT

    context.user_data['subject'] = subject
    await update.message.reply_text(f"Предмет {subject} выбран. Введи задание (максимум 20 символов):")
    return TASK_INPUT

# Обработка ввода задания
async def task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text

    if len(task) > 20:
        await update.message.reply_text("Ошибка: задание не должно превышать 20 символов.")
        return TASK_INPUT

    month_year = context.user_data['month']
    day = context.user_data['day']
    subject = context.user_data['subject']

    # Добавляем задание
    if day not in homework[month_year]:
        homework[month_year][day] = []
    homework[month_year][day].append(f"{subject}: {task}")

    await update.message.reply_text(f"Задание по {subject} на {day} ({month_year}) добавлено: {task}")

    # Возврат на главную страницу
    await start(update, context)
    return ConversationHandler.END

# Команда для отображения всех домашних заданий за текущий месяц
async def show_all_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_date = get_current_month_year()
    current_month_year = current_date.strftime('%B %Y')
    if current_month_year in homework and homework[current_month_year]:
        all_homework = []
        for day in range(1, 32):
            day_str = str(day)
            if day_str in homework[current_month_year]:
                tasks = ', '.join(homework[current_month_year][day_str])
                all_homework.append(f"{day}: {tasks}")

        if all_homework:
            await update.message.reply_text(f"Все домашние задания на {current_month_year}:\n" + "\n".join(all_homework))
        else:
            await update.message.reply_text(f"Нет домашних заданий на {current_month_year}.")
    else:
        await update.message.reply_text(f"Нет домашних заданий на {current_month_year}.")
    await start(update, context)

# Функция для получения домашней работы за конкретный день
async def get_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создание кнопок для выбора месяца
    current_date = get_current_month_year()
    current_month_year = current_date.strftime('%B %Y')
    months_keyboard = [
        ['Предыдущий месяц'],
        [current_month_year],
        ['Следующий месяц'],
        ['Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(months_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выбери месяц:", reply_markup=reply_markup)
    return MONTH_REQUEST

# Обработка выбора месяца для получения домашних заданий
async def month_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_month = update.message.text
    current_date = get_current_month_year()
    current_month_year = current_date.strftime('%B %Y')

    if selected_month == 'Назад':
        await start(update, context)
        return ConversationHandler.END

    month_year = current_month_year  # Инициализация переменной month_year

    if selected_month == 'Следующий месяц':
        next_month_date = current_date + timedelta(days=31)
        month_year = next_month_date.strftime('%B %Y')
    elif selected_month == 'Предыдущий месяц':
        prev_month_date = current_date - timedelta(days=31)
        month_year = prev_month_date.strftime('%B %Y')

    context.user_data['month_year'] = month_year
    await update.message.reply_text("Теперь введи день (1-31):")
    return DAY_REQUEST

# Обработка ввода дня для получения домашних заданий
async def day_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    month_year = context.user_data['month_year']

    if not day.isdigit() or int(day) < 1 or int(day) > 31:
        await update.message.reply_text("Ошибка: введите корректный день (от 1 до 31).")
        return DAY_REQUEST

    day_str = str(day)

    if month_year in homework and day_str in homework[month_year]:
        tasks = ', '.join(homework[month_year][day_str])
        await update.message.reply_text(f"Задания на {day} {month_year}:\n{tasks}")
    else:
        await update.message.reply_text(f"Нет домашних заданий на {day} {month_year}.")
    
    await start(update, context)
    return ConversationHandler.END

# Выбор месяца для редактирования домашнего задания
async def edit_select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_status = context.user_data.get('status', USER)
    if user_status != ADMIN:
        await update.message.reply_text("У вас нет прав для редактирования домашних заданий.")
        return ConversationHandler.END
    
    current_date = get_current_month_year()
    current_month_year = current_date.strftime('%B %Y')
    months_keyboard = [
        ['Предыдущий месяц'],
        [current_month_year],
        ['Следующий месяц'],
        ['Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(months_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выбери месяц для редактирования:", reply_markup=reply_markup)
    return EDIT_MONTH_SELECTION

# Обработка выбора месяца для редактирования
async def edit_month_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_month = update.message.text
    current_date = get_current_month_year()
    month_year = current_date.strftime('%B %Y')

    if selected_month == 'Назад':
        await start(update, context)
        return ConversationHandler.END

    if selected_month == 'Следующий месяц':
        next_month_date = current_date + timedelta(days=31)
        month_year = next_month_date.strftime('%B %Y')
    elif selected_month == 'Предыдущий месяц':
        prev_month_date = current_date - timedelta(days=31)
        month_year = prev_month_date.strftime('%B %Y')

    context.user_data['edit_month'] = month_year  # Сохраняем выбранный месяц для редактирования
    await update.message.reply_text("Теперь введи день (1-31):")
    return EDIT_DAY_INPUT

# Обработка ввода дня для редактирования
async def edit_day_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    month_year = context.user_data['edit_month']

    if not day.isdigit() or int(day) < 1 or int(day) > 31:
        await update.message.reply_text("Ошибка: введите корректный день (от 1 до 31).")
        return EDIT_DAY_INPUT

    day_str = str(day)

    if month_year in homework and day_str in homework[month_year]:
        # Выводим текущие задания
        tasks = homework[month_year][day_str]
        await update.message.reply_text(f"Задания на {day} {month_year}:\n" + "\n".join(tasks) + "\n\nВыбери предмет для редактирования:")
        
        subjects_keyboard = list(set(task.split(':')[0] for task in tasks))  # Уникальные предметы
        subjects_keyboard.append('Назад')
        reply_markup = ReplyKeyboardMarkup([[subject] for subject in subjects_keyboard], one_time_keyboard=True)
        await update.message.reply_text("Выбери предмет для редактирования:", reply_markup=reply_markup)
        context.user_data['edit_day'] = day_str  # Сохраняем день для редактирования
        return EDIT_SUBJECT_SELECTION
    else:
        await update.message.reply_text(f"Нет домашних заданий на {day} {month_year}.")
        await start(update, context)
        return ConversationHandler.END

# Обработка выбора предмета для редактирования
async def edit_subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text

    if subject == 'Назад':
        await edit_day_input(update, context)
        return EDIT_DAY_INPUT

    context.user_data['edit_subject'] = subject
    await update.message.reply_text(f"Выбран предмет {subject}. Введи новое задание (максимум 20 символов):")
    return EDIT_TASK_INPUT

# Обработка ввода нового задания для редактирования
async def edit_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_task = update.message.text

    if len(new_task) > 20:
        await update.message.reply_text("Ошибка: задание не должно превышать 20 символов.")
        return EDIT_TASK_INPUT

    month_year = context.user_data['edit_month']
    day_str = context.user_data['edit_day']
    subject = context.user_data['edit_subject']

    # Удаляем старое задание и добавляем новое
    tasks = homework[month_year][day_str]
    homework[month_year][day_str] = [f"{subject}: {new_task}" if task.startswith(subject) else task for task in tasks]

    await update.message.reply_text(f"Задание по {subject} на {day_str} ({month_year}) обновлено: {new_task}")
    await start(update, context)
    return ConversationHandler.END

# Основная функция
def main():
    app = ApplicationBuilder().token("7568107888:AAE3V5xpJ2sL2SSUxS23vonRkkrLNnZPNwM").build()

    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", select_month)],
        states={
            MONTH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, month_selection)],
            DAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_input)],
            SUBJECT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, subject_selection)],
            TASK_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_input)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    edit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_select_month)],
        states={
            EDIT_MONTH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_month_selection)],
            EDIT_DAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_day_input)],
            EDIT_SUBJECT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_subject_selection)],
            EDIT_TASK_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_task_input)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    get_homework_handler = ConversationHandler(
        entry_points=[CommandHandler("get_homework", get_homework)],
        states={
            MONTH_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, month_request)],
            DAY_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_request)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_status", set_status))  # Установка статуса
    app.add_handler(CommandHandler("all", show_all_homework))  # Команда для просмотра всех домашних заданий
    app.add_handler(add_conv_handler)
    app.add_handler(edit_conv_handler)  # Добавление команды для редактирования домашних заданий
    app.add_handler(get_homework_handler)  # Добавление команды для получения домашней работы за конкретный день

    app.run_polling()

if __name__ == "__main__":
    main()
