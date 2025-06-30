import os
import json
import pandas as pd
from telebot import TeleBot, types
from dotenv import load_dotenv
import re

# Constants
CANCEL_BUTTON = "Відмінити реєстрацію"

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
raw_admin = os.getenv("ADMIN_CHAT_ID", "")
try:
    ADMIN_CHAT_ID = int(raw_admin)
except ValueError:
    print("❌ Помилка: ADMIN_CHAT_ID має бути числом у .env")
    ADMIN_CHAT_ID = None

if not TOKEN:
    print("❌ Помилка: не знайдено TELEGRAM_BOT_TOKEN у .env")
    exit(1)

# Посилання на Monobank
MONO_LINK = "https://send.monobank.ua/jar/24F7gJ3cw5"

# Особисті реквізити ПриватБанку
PRIVAT_CARD = "5168 7520 2133 7889"
PRIVAT_IBAN = "UA52 305299 0262 0364 0092 5651653"
RECEIVER    = "Семенюк Андрій Олександрович"

# Initialize bot
bot = TeleBot(TOKEN)

bot.set_my_commands([
    types.BotCommand("start",    "Привітання та інструкції"),
    types.BotCommand("questions","Готові питання"),
    types.BotCommand("number",   "Контактний номер"),
    types.BotCommand("donate",   "Пожертвування"),
    types.BotCommand("register", "Реєстрація дитини")
])

DATA_DIR      = 'data'
REGISTER_JSON = os.path.join(DATA_DIR, 'registrations.json')
REGISTER_XLSX = os.path.join(DATA_DIR, 'registrations.xlsx')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if os.path.exists(REGISTER_JSON):
    with open(REGISTER_JSON, 'r', encoding='utf-8') as f:
        registrations = json.load(f)
else:
    registrations = []

user_data = {}

# === Валідація ===
def is_valid_name(text):
    parts = text.strip().split()
    if len(parts) < 2:
        return False
    for part in parts:
        if not re.match(r"^[А-ЯІЇЄҐ][а-яіїєґ’'-]+$", part):
            return False
    return True

def is_valid_phone(text):
    return bool(re.match(r"^(?:\+?38)?0\d{9}$", text.strip()))

def is_valid_age(text):
    try:
        age = int(text)
        return 5 <= age <= 16
    except:
        return False

def is_valid_needs(text):
    return len(text.strip()) <= 100

# === Утиліта: повідомлення з кнопкою скасування ===
def send_with_cancel(chat_id, text):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(CANCEL_BUTTON)
    bot.send_message(chat_id, text, reply_markup=keyboard)

# === Обробка скасування ===
@bot.message_handler(func=lambda m: m.text == CANCEL_BUTTON)
def handle_cancel(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data.pop(chat_id)
        bot.send_message(chat_id, "❌ Реєстрацію скасовано.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, "Нема активної сесії.", reply_markup=types.ReplyKeyboardRemove())

# === Команди ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_data.pop(chat_id, None)
    bot.send_message(
        chat_id,
        "👋 Вітаю! Я — бот дитячого табору 2025.\n"
        "/questions — готові питання\n"
        "/register — зареєструвати дитину на табір\n"
        "/donate — підтримати нас платежем",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(commands=['questions'])
def handle_questions(message):
    chat_id = message.chat.id
    user_data.pop(chat_id, None)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Розклад", "Вартість", "Що брати", "Номер телефону", "Інше питання")
    bot.send_message(chat_id, "Оберіть питання:", reply_markup=keyboard)

@bot.message_handler(commands=['number'])
def handle_number(message):
    chat_id = message.chat.id
    user_data.pop(chat_id, None)
    bot.send_message(chat_id, "📞 Контактний номер: 0689376905 (Андрій)", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['donate'])
def handle_donate(message):
    chat_id = message.chat.id
    user_data.pop(chat_id, None)
    bot.send_message(chat_id, "💚 Дякуємо за вашу підтримку!", reply_markup=types.ReplyKeyboardRemove())
    inline = types.InlineKeyboardMarkup(row_width=2)
    inline.add(
        types.InlineKeyboardButton(text="Monobank", url=MONO_LINK),
        types.InlineKeyboardButton(text="ПриватБанк ▶️", callback_data="show_privat")
    )
    bot.send_message(chat_id, "Оберіть спосіб переказу:", reply_markup=inline)

@bot.callback_query_handler(func=lambda c: c.data == 'show_privat')
def show_privat_data(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    bot.edit_message_reply_markup(chat_id, callback_query.message.message_id, reply_markup=None)
    text = (
        f"💳 *ПриватБанк*\n\n"
        f"Картка: `{PRIVAT_CARD}`\n"
        f"IBAN: `{PRIVAT_IBAN}`\n"
        f"Отримувач: _{RECEIVER}_\n\n"
        "🔄 Скопіюйте ці дані в свій Privat24 чи інший банк для переказу."
    )
    bot.send_message(chat_id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "Розклад")
def answer_schedule(message):
    bot.send_message(message.chat.id, "🗓 Наш табір працює з 5 по 7 серпня, 9:00–18:00.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Вартість")
def answer_price(message):
    bot.send_message(message.chat.id, "💵 Благодійний табір; підтримати можна через /donate.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Що брати")
def answer_packing(message):
    bot.send_message(message.chat.id, "🎒 Зручний одяг, кепка та гарний настрій.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Номер телефону")
def answer_phone(message):
    bot.send_message(message.chat.id, "📞 0689376905 (Андрій)", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Інше питання")
def handle_custom_question(message):
    msg = bot.send_message(message.chat.id, "Напишіть ваше питання:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(message.chat.id, "✅ Дякую! Ми відповімо.")
    if ADMIN_CHAT_ID:
        bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)

# === Реєстрація ===
@bot.message_handler(commands=['register'])
def cmd_register(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'children': []}
    send_with_cancel(chat_id, "👪 Ім'я та Прізвище батька/матері:")
    bot.register_next_step_handler(message, process_parent_name)

def process_parent_name(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    if not is_valid_name(message.text):
        send_with_cancel(chat_id, "❌ Введіть коректне ім’я та прізвище (наприклад, 'Гаврилюк Оля').")
        return bot.register_next_step_handler(message, process_parent_name)
    user_data[chat_id]['parent_name'] = message.text.strip()
    send_with_cancel(chat_id, "Телефон батьків:")
    bot.register_next_step_handler(message, process_parent_phone)

def process_parent_phone(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    if not is_valid_phone(message.text):
        send_with_cancel(chat_id, "❌ Введіть телефон у форматі 0XXXXXXXXX або +380XXXXXXXXX.")
        return bot.register_next_step_handler(message, process_parent_phone)
    user_data[chat_id]['parent_phone'] = message.text.strip()
    send_with_cancel(chat_id, "Скільки дітей? Введіть число:")
    bot.register_next_step_handler(message, process_child_count)

def process_child_count(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    try:
        count = int(message.text)
        assert count > 0
    except:
        send_with_cancel(chat_id, "Введіть коректне число дітей:")
        return bot.register_next_step_handler(message, process_child_count)
    user_data[chat_id]['child_count'] = count
    user_data[chat_id]['current_child'] = 1
    ask_child_info(chat_id)

def ask_child_info(chat_id):
    idx = user_data[chat_id]['current_child']
    send_with_cancel(chat_id, f"Ім'я та Прізвище дитини №{idx}:")
    bot.register_next_step_handler_by_chat_id(chat_id, process_child_name)

def process_child_name(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    if not is_valid_name(message.text):
        send_with_cancel(chat_id, "❌ Введіть коректне ім’я дитини (наприклад, 'Іваненко Петро').")
        return bot.register_next_step_handler(message, process_child_name)
    user_data[chat_id]['children'].append({'name': message.text.strip()})
    send_with_cancel(chat_id, "Вік дитини:")
    bot.register_next_step_handler(message, process_child_age)

def process_child_age(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    if not is_valid_age(message.text):
        send_with_cancel(chat_id, "❌ Введіть вік дитини від 5 до 16.")
        return bot.register_next_step_handler(message, process_child_age)
    user_data[chat_id]['children'][-1]['age'] = int(message.text)
    send_with_cancel(chat_id, "Особливості/алергії? Якщо ні — 'Ні':")
    bot.register_next_step_handler(message, process_child_needs)

def process_child_needs(message):
    if message.text == CANCEL_BUTTON:
        return handle_cancel(message)
    chat_id = message.chat.id
    if not is_valid_needs(message.text):
        send_with_cancel(chat_id, "❌ Будь ласка, скоротіть опис до 100 символів.")
        return bot.register_next_step_handler(message, process_child_needs)
    user_data[chat_id]['children'][-1]['needs'] = message.text.strip()
    if user_data[chat_id]['current_child'] < user_data[chat_id]['child_count']:
        user_data[chat_id]['current_child'] += 1
        ask_child_info(chat_id)
    else:
        finalize_registration(chat_id)

def finalize_registration(chat_id):
    entry = user_data.pop(chat_id)
    registrations.append(entry)
    with open(REGISTER_JSON, 'w', encoding='utf-8') as f:
        json.dump(registrations, f, ensure_ascii=False, indent=2)
    df = pd.json_normalize(registrations, 'children', ['parent_name', 'parent_phone', 'child_count'])
    df.to_excel(REGISTER_XLSX, index=False)
    bot.send_message(chat_id, "✅ Реєстрація завершена!", reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(
        chat_id,
        "📣 Долучайтесь до батьківської групи табору 2025: [t.me/tabir_parents](https://t.me/tabir_parents)",
        parse_mode='Markdown'
    )
    if ADMIN_CHAT_ID:
        summary = f"Нова реєстрація від {entry['parent_name']} ({entry['parent_phone']})"
        for i, c in enumerate(entry['children'], 1):
            summary += f"\n{i}. {c['name']}, вік {c['age']}, {c['needs']}"
        bot.send_message(ADMIN_CHAT_ID, summary)

# Run bot
if __name__ == '__main__':
    print("🚀 Бот стартує…")
    bot.infinity_polling(timeout=60)
