from telebot import types
from database import add_user, get_user, update_subgroup
from database import add_to_queue

registered_users = {}

def register_handlers(bot):
    pending_labs = {}

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('Зарегистрироваться'), types.KeyboardButton('Выбрать подгруппу'))
        markup.row(types.KeyboardButton('Посмотреть информацию о себе'), types.KeyboardButton('Записаться в очередь'))
        markup.row(types.KeyboardButton('Вывести очередь на лабы'))
        bot.send_message(message.chat.id, "Привет! Я бот для записи в очередь. Чтобы записаться напиши /queue или выбери соотвествующий пункт в меню", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == 'Зарегистрироваться')
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
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь через меню или команду /queue")
            return
        markup = types.InlineKeyboardMarkup()
        subgroupbtn1 = types.InlineKeyboardButton('1', callback_data='subgroup_1')
        subgroupbtn2 = types.InlineKeyboardButton('2', callback_data='subgroup_2')
        markup.row(subgroupbtn1, subgroupbtn2)
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

    pending_labs = {}

    @bot.message_handler(func=lambda message: message.text == 'Записаться в очередь')
    def select_lab(message):
        user_id = message.from_user.id
        if not get_user(user_id):
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь через меню или команду /queue")
            return

        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(str(i), callback_data=f'number_of_lab_{i}') for i in range(1, 9)]
        markup.row(*buttons[:4])
        markup.row(*buttons[4:])
        bot.send_message(message.chat.id, "Выберите номер лабораторной работы ...", reply_markup=markup,
                         parse_mode='HTML')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('number_of_lab_'))
    def sign_up_for_lab(call):
        user_id = call.from_user.id
        lab_number = call.data.split('_')[-1]

        user_data = get_user(user_id)
        if not user_data:
            bot.answer_callback_query(call.id, "Сначала зарегистрируйтесь!", show_alert=True)
            return

        fi, subgroup = user_data
        if not subgroup:
            bot.answer_callback_query(call.id, "Сначала выберите подгруппу!", show_alert=True)
            return

        if user_id in pending_labs:
            bot.answer_callback_query(call.id, "Вы уже начали запись. Отправьте файл или ссылку.", show_alert=True)
            return

        pending_labs[user_id] = lab_number
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                         f"📥 Пожалуйста, отправьте <b>.exe файл</b> или <b>ссылку на GitHub</b> для лабораторной №{lab_number}.",
                         parse_mode='HTML')

    @bot.message_handler(content_types=['document', 'text'])
    def handle_submission(message):
        user_id = message.from_user.id

        if user_id not in pending_labs:
            return

        lab_number = pending_labs[user_id]

        if message.content_type == 'document':
            if not message.document.file_name.endswith('.exe'):
                bot.send_message(message.chat.id, "⚠ Пожалуйста, отправьте .exe файл или ссылку на GitHub.")
                return
            submission = f"[Файл] {message.document.file_name}"

        elif message.content_type == 'text':
            if "github.com" not in message.text:
                bot.send_message(message.chat.id, "⚠ Пожалуйста, отправьте ссылку на GitHub или .exe файл.")
                return
            submission = f"[GitHub] {message.text}"

        else:
            bot.send_message(message.chat.id, "⚠ Неверный формат. Отправьте .exe файл или GitHub ссылку.")
            return

        fi, subgroup = get_user(user_id)
        success = add_to_queue(user_id, fi, subgroup, lab_number)

        if success:
            bot.send_message(message.chat.id,
                             f"✅ Вы успешно записались на лабораторную №<b>{lab_number}</b>\n{submission}",
                             parse_mode='HTML')
        else:
            bot.send_message(message.chat.id,
                             f"⚠ Вы уже записаны на лабораторную №{lab_number}.",
                             parse_mode='HTML')

        del pending_labs[user_id]
