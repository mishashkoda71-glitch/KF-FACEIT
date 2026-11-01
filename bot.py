import telebot
from telebot import types
import random
import string
import os  # Импортируем библиотеку для работы с секретами

# Берем данные из защищенных переменных сервера
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

bot = telebot.TeleBot(TOKEN)

queue = []
users_db = {}

def get_user(user_id, username):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": username, "elo": 1000, "matches": 0, "wins": 0, "is_banned": False
        }
    return users_db[user_id]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_play = types.InlineKeyboardButton("🎮 Найти матч", callback_data="menu_play")
    btn_profile = types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile")
    btn_top = types.InlineKeyboardButton("🏆 Топ игроков", callback_data="menu_top")
    btn_tiktok = types.InlineKeyboardButton("🎵 Наш TikTok", url="https://tiktok.com/@kffaceit") 
    
    markup.add(btn_play, btn_profile, btn_top)
    markup.add(btn_tiktok)
    
    text = "Добро пожаловать в KF-Faceit! 🎮\nТвоя площадка для поиска матчей в **CounterFlame**.\n\nВыбери действие:"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "menu_profile":
        user = get_user(call.from_user.id, call.from_user.username)
        status = "🔴 ЗАБАНЕН" if user['is_banned'] else "🟢 Активен"
        text = f"👤 **Профиль:** @{user['name']}\nСтатус: {status}\n📊 **ELO:** {user['elo']}\n🎮 **Матчи:** {user['matches']}"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_top":
        sorted_users = sorted(users_db.values(), key=lambda x: x['elo'], reverse=True)[:5]
        top_text = "🏆 **Топ-5 игроков KF-Faceit:**\n\n"
        for i, u in enumerate(sorted_users, 1):
            top_text += f"{i}. @{u['name']} — {u['elo']} ELO\n"
        bot.send_message(call.message.chat.id, top_text, parse_mode='Markdown')

    elif call.data == "menu_play":
        add_to_queue(call.message.chat.id, call.from_user.id, call.from_user.username)
        
    elif call.data == "menu_leave":
        leave_queue(call.message.chat.id, call.from_user.id)

def add_to_queue(chat_id, user_id, username):
    user = get_user(user_id, username)
    if user['is_banned']:
        bot.send_message(chat_id, "❌ Вы забанены на платформе KF-Faceit!")
        return
    if user_id in queue:
        bot.send_message(chat_id, "Ты уже в очереди! Ожидай.")
        return
    
    queue.append(user_id)
    
    markup = types.InlineKeyboardMarkup()
    btn_leave = types.InlineKeyboardButton("❌ Выйти из очереди", callback_data="menu_leave")
    markup.add(btn_leave)
    
    bot.send_message(chat_id, f"Игрок @{username} в очереди. ({len(queue)}/10)", reply_markup=markup)
    
    if len(queue) >= 10:
        room_code = "KF-" + ''.join(random.choices(string.digits, k=4))
        players_to_tag = ""
        for uid in queue:
            name = users_db[uid]['name']
            players_to_tag += f"@{name} "
        
        bot.send_message(chat_id, f"🔥 **МАТЧ НАЙДЕН!** 🔥\n\nИгроки: {players_to_tag}\n\n🔑 **Код лобби:** `{room_code}`\nСоздайте комнату в CounterFlame и введите этот код!", parse_mode='Markdown')
        queue.clear()

def leave_queue(chat_id, user_id):
    if user_id in queue:
        queue.remove(user_id)
        bot.send_message(chat_id, "Ты вышел из очереди.")
    else:
        bot.send_message(chat_id, "Тебя нет в очереди.")

@bot.message_handler(commands=['profile'])
def profile(message):
    user = get_user(message.from_user.id, message.from_user.username)
    status = "🔴 ЗАБАНЕН" if user['is_banned'] else "🟢 Активен"
    text = f"👤 **Профиль:** @{user['name']}\nСтатус: {status}\n📊 **ELO:** {user['elo']}\n🎮 **Матчи:** {user['matches']}"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['top'])
def top_cmd(message):
    sorted_users = sorted(users_db.values(), key=lambda x: x['elo'], reverse=True)[:5]
    top_text = "🏆 **Топ-5 игроков KF-Faceit:**\n\n"
    for i, u in enumerate(sorted_users, 1):
        top_text += f"{i}. @{u['name']} — {u['elo']} ELO\n"
    bot.reply_to(message, top_text, parse_mode='Markdown')

@bot.message_handler(commands=['ban'])
def ban(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет прав.")
        return
    try:
        target_id = int(message.text.split()[1])
        if target_id in users_db:
            users_db[target_id]['is_banned'] = True
            bot.reply_to(message, f"🔨 Игрок {target_id} забанен!")
        else:
            bot.reply_to(message, "Игрок не найден.")
    except:
        bot.reply_to(message, "Используй: /ban ID_игрока")

@bot.message_handler(commands=['unban'])
def unban(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет прав.")
        return
    try:
        target_id = int(message.text.split()[1])
        if target_id in users_db:
            users_db[target_id]['is_banned'] = False
            bot.reply_to(message, f"✅ Игрок {target_id} разбанен!")
        else:
            bot.reply_to(message, "Игрок не найден.")
    except:
        bot.reply_to(message, "Используй: /unban ID_игрока")

print("Бот KF-Faceit запущен и защищен!")
bot.polling()
