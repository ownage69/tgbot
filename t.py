import telebot
from telebot import types

API_TOKEN = '7960470111:AAHnjdL2z36goN4Hn2EnMj77fUHmMpCkdwQ'
bot = telebot.TeleBot(API_TOKEN)

registered_users = {}

# Обработка /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """
Привет, я бот для записи в очередь. Чтобы начать работу напиши /queue или выбери соответствующий пункт в меню
""")

# Обработка /queue
@bot.message_handler(commands=['queue'])
def send_queuemessage(message):
    user_id = message.from_user.id
    if user_id in registered_users:
        fi = registered_users[user_id]['fi']
        bot.reply_to(message, f"Ты уже записан как <b>{fi}</b>", parse_mode="HTML")
    else:
        bot.reply_to(message, f"<b>{message.from_user.first_name}</b>, напиши пожалуйста свою фамилию и имя (ровно два слова)", parse_mode="HTML")

# Обработка записи фамилии и имени
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def register_user(message):
    user_id = message.from_user.id

    if user_id in registered_users:
        bot.reply_to(message, "Ты уже зарегистрирован. Напиши /info для просмотра данных")
        return

    words = message.text.strip().split()
    if len(words) != 2:
        bot.reply_to(message, "Ошибка! Напиши фамилию и имя (ровно два слова)")
    else:
        registered_users[user_id] = {
            'fi': message.text.strip(),
            'subgroup': None
        }
        bot.reply_to(message, f"Отлично! Записал тебя как <b>{message.text.strip()}</b>", parse_mode="HTML")

# Обработка /subgroup
@bot.message_handler(commands=['subgroup'])
def subgroup_info(message):
    user_id = message.from_user.id
    if user_id not in registered_users:
        bot.reply_to(message, "Сначала зарегистрируйся через /queue")
        return

    markup = types.InlineKeyboardMarkup()
    btnsubgroup1 = types.InlineKeyboardButton('1', callback_data='subgroup_1')
    btnsubgroup2 = types.InlineKeyboardButton('2', callback_data='subgroup_2')
    markup.row(btnsubgroup1, btnsubgroup2)
    bot.reply_to(message, "Выбери номер подгруппы", reply_markup=markup)

# Запись в подгруппу
@bot.callback_query_handler(func=lambda call: call.data.startswith('subgroup_'))
def handle_subgroup_selection(call):
    user_id = call.from_user.id
    if user_id not in registered_users:
        bot.answer_callback_query(call.id, "Сначала зарегистрируйтесь")
        return

    selected = call.data.split('_')[1]
    registered_users[user_id]['subgroup'] = selected
    bot.answer_callback_query(call.id, f"Вы выбрали подгруппу {selected}")
    bot.send_message(call.message.chat.id, f"Вы записаны в подгруппу {selected} ✓")

# Обработка /info
@bot.message_handler(commands=['info'])
def info_about_user(message):
    user_id = message.from_user.id
    if user_id not in registered_users:
        bot.reply_to(message, "Вы ещё не зарегистрированы")
    else:
        fi = registered_users[user_id]['fi']
        subgroup = registered_users[user_id]['subgroup']
        if subgroup is None:
            subgroup = "не выбрана"
        bot.reply_to(message, f"""Информация о <b>{message.from_user.first_name}</b>:
Записан в очереди как: <b>{fi}</b>
Номер подгруппы: <b>{subgroup}</b>""", parse_mode="HTML")

bot.infinity_polling()
