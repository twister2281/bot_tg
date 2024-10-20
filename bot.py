from babel.dates import format_date
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, timedelta

# Состояния для команды /add, /edit и /get_homework
MONTH_SELECTION, DAY_INPUT, SUBJECT_SELECTION, TASK_INPUT, MONTH_REQUEST, DAY_REQUEST, EDIT_MONTH_SELECTION, EDIT_DAY_INPUT, EDIT_SUBJECT_SELECTION, EDIT_TASK_INPUT = range(10)
DELETE_MONTH_SELECTION, DELETE_DAY_SELECTION, DELETE_SUBJECT_SELECTION = range(10, 13)

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
        f"Привет! Я бот для добавления и редактирования домашнего задания.\n"
        f"Ты в статусе: {user_status}.\n"
        "Мои команды:\n\n"
        "Редактирование (доступно только блатным, так сказать)\n"
        "/add - добавить дз\n"
        "/edit - редактировать выбранное дз\n"
        "/delete - удалить дз\n\n"
        "Посмотреть дз:\n"
        "/all - получить задание на месяц\n"
        "/week - получить задание на неделю\n"
        "/get_homework - получить задание за конкретный день"
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
    await update.message.reply_text(f"Предмет {subject} выбран. Введи задание (максимум  символов):")
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
        all_homework = [f"**{current_month_year}**"]  # Жирный текст для месяца
        for day in range(1, 32):
            day_str = str(day)
            if day_str in homework[current_month_year]:
                tasks = '\n'.join(homework[current_month_year][day_str])
                all_homework.append(f"{day}: {tasks}")
        
        if all_homework:
            await update.message.reply_text("\n\n".join(all_homework), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"Нет домашних заданий на **{current_month_year}**.", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Нет домашних заданий на **{current_month_year}**.", parse_mode='Markdown')

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
async def delete_select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_status = context.user_data.get('status', USER)
    if user_status != ADMIN:
        await update.message.reply_text("У вас нет прав для удаления домашних заданий.")
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
    await update.message.reply_text("Выбери месяц для удаления задания:", reply_markup=reply_markup)
    return DELETE_MONTH_SELECTION

# Обработка выбора месяца для удаления
async def delete_month_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['delete_month'] = month_year  # Сохраняем выбранный месяц
    await update.message.reply_text("Теперь введи день (1-31):")
    return DELETE_DAY_SELECTION

# Обработка выбора дня для удаления задания
async def delete_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    month_year = context.user_data['delete_month']

    if not day.isdigit() or int(day) < 1 or int(day) > 31:
        await update.message.reply_text("Ошибка: введите корректный день (от 1 до 31).")
        return DELETE_DAY_SELECTION

    day_str = str(day)

    if month_year in homework and day_str in homework[month_year]:
        tasks = homework[month_year][day_str]
        await update.message.reply_text(f"Задания на {day} {month_year}:\n" + "\n".join(tasks) + "\n\nВыбери предмет для удаления:")

        subjects_keyboard = list(set(task.split(':')[0] for task in tasks))  # Уникальные предметы
        subjects_keyboard.append('Назад')
        reply_markup = ReplyKeyboardMarkup([[subject] for subject in subjects_keyboard], one_time_keyboard=True)
        await update.message.reply_text("Выбери предмет для удаления:", reply_markup=reply_markup)
        context.user_data['delete_day'] = day_str  # Сохраняем день для удаления
        return DELETE_SUBJECT_SELECTION
    else:
        await update.message.reply_text(f"Нет домашних заданий на {day} {month_year}.")
        await start(update, context)
        return ConversationHandler.END

# Обработка выбора предмета для удаления задания
async def delete_subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    month_year = context.user_data['delete_month']
    day_str = context.user_data['delete_day']

    if subject == 'Назад':
        await delete_day_selection(update, context)
        return DELETE_DAY_SELECTION

    # Удаление задания по предмету
    if month_year in homework and day_str in homework[month_year]:
        tasks = homework[month_year][day_str]
        new_tasks = [task for task in tasks if not task.startswith(subject)]
        
        if new_tasks:
            homework[month_year][day_str] = new_tasks
        else:
            del homework[month_year][day_str]  # Удаляем день, если больше нет заданий

        await update.message.reply_text(f"Задание по {subject} на {day_str} ({month_year}) удалено.")
    else:
        await update.message.reply_text(f"Нет задания по {subject} на {day_str} {month_year}.")
    
    await start(update, context)
    return ConversationHandler.END

def get_week_range():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # Понедельник текущей недели
    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье текущей недели
    return start_of_week, end_of_week

# Функция для отображения домашнего задания на текущую неделю
async def show_week_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_date = datetime.now()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    week_homework = [f"**{start_of_week.strftime('%B %Y')}**"]  # Жирный текст для месяца
    for i in range(7):  # Проходим по дням недели
        day = (start_of_week + timedelta(days=i)).day
        day_str = str(day)
        month_year = start_of_week.strftime('%B %Y')

        if month_year in homework and day_str in homework[month_year]:
            tasks = '\n'.join(homework[month_year][day_str])
            week_homework.append(f"{day}: {tasks}")
    
    if week_homework:
        await update.message.reply_text("\n\n".join(week_homework), parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Нет домашних заданий на текущую неделю.", parse_mode='Markdown')

    await start(update, context)

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

    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_select_month)],
        states={
            DELETE_MONTH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_month_selection)],
            DELETE_DAY_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_day_selection)],
            DELETE_SUBJECT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_subject_selection)],
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
    app.add_handler(get_homework_handler)  
    app.add_handler(delete_conv_handler)
    app.add_handler(CommandHandler("week", show_week_homework)) 
    app.run_polling()


if __name__ == "__main__":
    main()
