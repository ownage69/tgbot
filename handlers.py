from telebot import types
from database import add_user, get_user, update_subgroup, add_to_queue, AVAILABLE_LABS, get_lab_queue_by_subgroup, get_user_labs, is_fi_taken

# Пользователи которые будут зарегистрированы
registered_users = {}

def register_handlers(bot):
    pending_labs = {}

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('Зарегистрироваться'), types.KeyboardButton('Выбрать подгруппу'))
        markup.row(types.KeyboardButton('Посмотреть информацию о себе'), types.KeyboardButton('Записаться в очередь'))
        markup.row(types.KeyboardButton('Вывести очередь на лабы'))
        bot.send_message(message.chat.id, "Привет! Я бот для записи в очередь. Для начала тебе надо зарегистрироваться. Нажми соответствующую кнопку в меню", reply_markup=markup)

    def save_fi(message):
        words = message.text.strip().split()
        if len(words) != 2:
            bot.send_message(message.chat.id, "Неверный формат. Введите фамилию и имя ещё раз.")
            bot.register_next_step_handler(message, save_fi)
            return

        fi = message.text.strip()
        user_id = message.from_user.id

        # Проверяем, не занято ли это ФИ у другого пользователя
        if is_fi_taken(fi):
            bot.send_message(message.chat.id, "Эти фамилия и имя уже зарегистрированы другим пользователем. Повторите попытку")
            bot.register_next_step_handler(message, save_fi)
            return

        add_user(user_id, fi)
        bot.send_message(message.chat.id, f"Записал вас как: <b>{fi}</b>", parse_mode='HTML')

    @bot.message_handler(commands=['remove'])
    def remove_from_queue(message):
        # Проверка: только админ может удалять (по Telegram ID)
        admin_id = 424895903  # ← сюда вставь свой Telegram ID
        if message.from_user.id != admin_id:
            bot.send_message(message.chat.id, "У вас нет прав для этой команды.")
            return

        try:
            _, user_id_str, lab_number = message.text.strip().split()
            user_id = int(user_id_str)
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат. Используйте:\n/remove <user_id> <lab_number>")
            return

        from database import remove_user_from_lab

        success = remove_user_from_lab(user_id, lab_number)
        if success:
            bot.send_message(message.chat.id, f"Пользователь {user_id} удалён из лабораторной №{lab_number}")
        else:
            bot.send_message(message.chat.id, "Такого пользователя в очереди нет или ошибка.")

    @bot.message_handler(func=lambda message: message.text == 'Зарегистрироваться')
    def queue_command(message):
        user_id = message.from_user.id
        if get_user(user_id):
            bot.send_message(message.chat.id, "Вы уже зарегистрированы")
        else:
            bot.send_message(message.chat.id, "Введите свою фамилию и имя <b>(два слова) (!) сменить в будущем будет нельзя</b>", parse_mode='HTML')
            bot.register_next_step_handler(message, save_fi)

    @bot.message_handler(func=lambda message: message.text == 'Вывести очередь на лабы')
    def show_queue(message):
        user_id = message.from_user.id
        user_data = get_user(user_id)

        if not user_data:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь!")
            return

        fi, subgroup = user_data
        rows = get_lab_queue_by_subgroup(subgroup)

        if not rows:
            bot.send_message(message.chat.id, "⛔ Очередь пуста для вашей подгруппы.")
            return

        queue_text = f"📋 Очередь на лабораторные (Подгруппа {subgroup}):\n"
        labs = {}

        for lab_number, student_fi in rows:
            if lab_number not in labs:
                labs[lab_number] = []
            labs[lab_number].append(student_fi)

        for lab_number in sorted(labs, key=lambda x: int(x)):
            queue_text += f"\n🔬 Лабораторная №{lab_number}:\n"
            for i, student_fi in enumerate(labs[lab_number], 1):
                queue_text += f"  {i}. {student_fi}\n"

        bot.send_message(message.chat.id, queue_text)

    @bot.message_handler(func=lambda message: message.text == 'Выбрать подгруппу')
    def choose_subgroup(message):
        user_id = message.from_user.id
        if not get_user(user_id):
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь через меню")
            return
        # Проверка, если подгруппа уже выбрана — запретить менять
        user_data = get_user(user_id)
        fi, subgroup = user_data
        if subgroup:
            bot.send_message(message.chat.id, f"Подгруппа уже выбрана: <b>{subgroup}</b>. Её изменить нельзя.",
                             parse_mode='HTML')
            return

        markup = types.InlineKeyboardMarkup()
        subgroupbtn1 = types.InlineKeyboardButton('1', callback_data='subgroup_1')
        subgroupbtn2 = types.InlineKeyboardButton('2', callback_data='subgroup_2')
        markup.row(subgroupbtn1, subgroupbtn2)
        bot.send_message(message.chat.id, "Выберите подгруппу (!) опять же сменить в будущем ее будет нельзя:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('subgroup_'))
    def handle_subgroup(call):
        user_id = call.from_user.id
        new_subgroup = call.data.split('_')[1]

        user_data = get_user(user_id)
        if not user_data:
            bot.answer_callback_query(call.id, "Сначала зарегистрируйтесь!", show_alert=True)
            return

        fi, current_subgroup = user_data
        if current_subgroup:
            bot.answer_callback_query(call.id, "Вы уже выбрали подгруппу, изменить нельзя!", show_alert=True)
            return

        update_subgroup(user_id, new_subgroup)
        bot.answer_callback_query(call.id, f"Подгруппа {new_subgroup} выбрана!")
        bot.send_message(call.message.chat.id, f"Вы записаны в подгруппу <b>{new_subgroup}</b>", parse_mode='HTML')

    @bot.message_handler(func=lambda message: message.text == 'Посмотреть информацию о себе')
    def show_info(message):
        user_id = message.from_user.id
        user_data = get_user(user_id)

        if not user_data:
            bot.send_message(message.chat.id, "Вы ещё не зарегистрированы!")
            return

        fi, subgroup = user_data

        user_labs = get_user_labs(user_id)  # Вот здесь вызываем функцию, чтобы получить список загруженных лаб

        if user_labs:
            labs_text = ", ".join(sorted(user_labs, key=int))
        else:
            labs_text = "Нет загруженных лаб"

        bot.send_message(
            message.chat.id,
            f"""👤 Вы: <b>{fi}</b>
👥 Подгруппа: <b>{subgroup}</b>
📚 Загруженные лабораторные: <b>{labs_text}</b>""",
            parse_mode='HTML'
        )

    pending_labs = {}

    @bot.message_handler(func=lambda message: message.text == 'Записаться в очередь')
    def select_lab(message):
        user_id = message.from_user.id
        if not get_user(user_id):
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь через меню")
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

        if lab_number not in AVAILABLE_LABS:
            bot.answer_callback_query(call.id, f"❌ Лабораторная №{lab_number} пока недоступна для записи.")
            return  # прекращаем выполнение

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
        result = add_to_queue(user_id, fi, subgroup, lab_number)

        if result == "not_available":
            bot.send_message(message.chat.id, f"❌ Лабораторная №{lab_number} пока недоступна для записи.")
        elif result is False:
            bot.send_message(message.chat.id, f"⚠ Вы уже записаны на лабораторную №{lab_number}.")
        else:
            bot.send_message(message.chat.id,
                             f"✅ Вы успешно записались на лабораторную №<b>{lab_number}</b>\n{submission}",
                             parse_mode='HTML')

        del pending_labs[user_id]
