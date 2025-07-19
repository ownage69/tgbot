from telebot import types
from database import add_user, get_user, update_subgroup

registered_users = {}

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('Записаться в очередь'))
        markup.row(types.KeyboardButton('Выбрать подгруппу'), types.KeyboardButton('Посмотреть информацию о себе'))
        bot.send_message(message.chat.id, "Привет! Я бот для записи в очередь. Чтобы записаться напиши /queue или выбери соотвествующий пункт в меню", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == 'Записаться в очередь')
    def queue_command(message):
        user_id = message.from_user.id
        if get_user(user_id):
            bot.send_message(message.chat.id, "Вы уже зарегистрированы")
        else:
            bot.send_message(message.chat.id, "Введите свою фамилию и имя <b>(два слова)</b>", parse_mode='HTML')
            bot.register_next_step_handler(message, save_fi)

    def save_fi(message):
        words = message.text.strip().split()
        if len(words) != 2:
            bot.send_message(message.chat.id, "Неверный формат. Введите фамилию и имя ещё раз.")
            bot.register_next_step_handler(message, save_fi)
            return
        user_id = message.from_user.id
        fi = message.text.strip()
        add_user(user_id, fi)
        bot.send_message(message.chat.id, f"Записал вас как: <b>{fi}</b>", parse_mode='HTML')

    @bot.message_handler(func=lambda message: message.text == 'Выбрать подгруппу')
    def choose_subgroup(message):
        user_id = message.from_user.id
        if not get_user(user_id):
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь через меню или команду /queue.")
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('1', callback_data='subgroup_1'))
        markup.add(types.InlineKeyboardButton('2', callback_data='subgroup_2'))
        bot.send_message(message.chat.id, "Выберите подгруппу:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('subgroup_'))
    def handle_subgroup(call):
        user_id = call.from_user.id
        subgroup = call.data.split('_')[1]
        update_subgroup(user_id, subgroup)
        bot.answer_callback_query(call.id, f"Подгруппа {subgroup} выбрана!")
        bot.send_message(call.message.chat.id, f"Вы записаны в подгруппу <b>{subgroup}</b>", parse_mode='HTML')

    @bot.message_handler(func=lambda message: message.text == 'Посмотреть информацию о себе')
    def show_info(message):
        user_id = message.from_user.id
        user_data = get_user(user_id)
        if user_data:
            fi, subgroup = user_data
            subgroup = subgroup if subgroup else "не выбрана"
            bot.reply_to(message, f"""Информация о <b>{message.from_user.first_name}</b>:
Записан в очереди как: <b>{fi}</b>
Номер подгруппы: <b>{subgroup}</b>""", parse_mode="HTML")

        else:
            bot.send_message(message.chat.id, "Вы ещё не зарегистрированы")
