from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Укажите путь к файлу credentials.json
GOOGLE_SHEETS_CREDS = 'D:/workspace/test_telegram_bot/date.json'

# Укажите ID вашей таблицы Google Sheets
GOOGLE_SHEETS_ID = '1kPZwQaWTLbfX334m6ux7ydsHVZzxuKqA5iVn25f0XZ4'

# Укажите токен вашего Telegram-бота
TELEGRAM_TOKEN = '6308490851:AAE-4tciE3Gn0oNgjz7IeqMbRsIxWuJs7Rs'



# Создаем экземпляр для работы с Google Sheets
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS)
client = gspread.authorize(credentials)
sheet = client.open_by_key(GOOGLE_SHEETS_ID).sheet1

# Создаем экземпляр для работы с Telegram
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот напоминаний.")


def remind_manager(context):
    job = context.job
    tel_id, text, date, time, answer_time = job.context

    # Отправляем сообщение сотруднику и прикрепленной клавиатурой
    keyboard = [[InlineKeyboardButton("Выполнено", callback_data='done'),
                 InlineKeyboardButton("Не сделано", callback_data='not_done')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=tel_id, text=text, reply_markup=reply_markup)

    # Записываем данные в Google Sheets
    row = [str(datetime.datetime.now()), text, date, time, '']
    sheet.append_row(row)

    # Планируем задачу проверки ответа от сотрудника
    context.job_queue.run_once(check_response, answer_time, context=(tel_id, len(sheet.col_values(1))))


def check_response(context):
    job = context.job
    tel_id, start_row = job.context
    current_row = len(sheet.col_values(1))

    if current_row > start_row:
        response = sheet.cell(current_row, 5).value

        # Проверяем ответ сотрудника и отправляем сообщение менеджеру
        if response == 'done':
            context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник выполнел задание.")
        elif response == 'not_done':
            context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник не выполнил задание.")
        else:
            context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник проигнорировал задание.")
    else:
        # Если сотрудник не ответил вовремя
        context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник проигнорировал задание.")


def button(update, context):
    query = update.callback_query
    query.answer()

    # Обновляем ответ сотрудника в Google Sheets
    row = int(query.data)
    sheet.update_cell(row, 5, query.data)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо за ваш ответ!")


# Регистрируем обработчики команд и событий
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(button))

updater.start_polling()
