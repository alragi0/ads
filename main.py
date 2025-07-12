import telebot
from telebot import types
import sqlite3
from config import cfg
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, LabeledPrice

API_TOKEN = cfg.BOT_TOKEN
ADMIN_ID = cfg.SUDO # Replace with your Telegram user ID
CHANNEL_ID = cfg.CHID
CHANNEL_USERNAME = cfg.FSUB
NAME_AUCTION = cfg.NAME_AUCTION

bot = telebot.TeleBot(API_TOKEN, parse_mode='Markdown')
conn = sqlite3.connect('nft_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Database setup
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, url TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)''')
conn.commit()

def is_banned(user_id):
    cursor.execute("SELECT * FROM banned WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def add_user(user):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user.id, user.username))
    conn.commit()

@bot.message_handler(commands=['start'])
def start(message: Message):
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "أنت محظور من استخدام هذا البوت.")
        return
    add_user(message.from_user)

    markup = types.InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("شروط النشر  .", callback_data="AFC"),
               InlineKeyboardButton("نشر مزاد .", callback_data="Great_ads"))
    markup.add(InlineKeyboardButton(f"{NAME_AUCTION}", url=f"https://t.me/{CHANNEL_USERNAME}"))
    text = f"👋🏻|مرحباً بك،{message.from_user.full_name}\n\nيمكنك المشاركة في المزاد عن طريق الضغط على 'نشر مزاد' من الأسفل والانضمام إلى المجموعة. نحن في انتظار مساهماتك ومشاركتك في المزاد!"
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "AFC")
def handle_ASC(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("رجوع .", callback_data="cancel"))
    
    text = """~ نوافق على المُعرفات المرتبة ✓.

- يكون المعرف على قناة فارغة مابيها معرف تواصل فقط معرف قناة المزاد مِثال - ( المزاد هنا @mmmzm ).

- ارسل مُعرفك الى الزر الخاص به ( ملكية - NFT - مقتنى ).

- عدم تضمين اي طريقة للتواصل في داخل قناة المعرف. 

- اذا يوجد مزاد ثاني في قناة المعرف ما ينشر مُعرفك.

- لبدء نشر مزادك اضغط 'نشر مزاد' واختر نوع المزاد وارسل الرابط إذا كان مقتنى رقمي، ومعرف اذا كان يوزر.
Channel : @mmmzm
Owner : @ddddi"""

    bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_ASC(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("شروط النشر  .", callback_data="AFC"),
               InlineKeyboardButton("نشر مزاد .", callback_data="Great_ads"))
    markup.add(InlineKeyboardButton(f"{NAME_AUCTION}", url=f"https://t.me/{CHANNEL_USERNAME}"))
    text = f"👋🏻|مرحباً بك،{call.from_user.full_name}\n\nيمكنك المشاركة في المزاد عن طريق الضغط على 'نشر مزاد' من الأسفل والانضمام إلى المجموعة. نحن في انتظار مساهماتك ومشاركتك في المزاد!"
    bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)
    return

@bot.callback_query_handler(func=lambda call: call.data == "Great_ads")
def handle_ASC(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎁 هدية NFT", callback_data="type_gift"))
    markup.add(types.InlineKeyboardButton("👤 يوزر NFT", callback_data="type_user_nft"),
               types.InlineKeyboardButton("🏆 يوزر ملكية", callback_data="type_user_premium"))
    markup.add(types.InlineKeyboardButton("رجوع .", callback_data="cancel"))
    text = "- أختار نوع الاعلان : "
    bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)
    return






@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type_selection(call):
    ad_type = {
        "type_gift": "🎁 هدية NFT",
        "type_user_nft": "👤 يوزر NFT",
        "type_user_premium": "🏆 يوزر ملكية"
    }.get(call.data, "غير معروف")
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"أرسل رابط {ad_type}:")
    bot.register_next_step_handler(call.message, lambda msg: save_request(msg, ad_type))


@bot.message_handler(func=lambda message: message.text in ["🎁 هدية NFT", "👤 يوزر NFT", "🏆 يوزر ملكي"])
def request_url(message):
    bot.send_message(message.chat.id, "أرسل رابط الهدية أو القناة:")
    bot.register_next_step_handler(message, lambda msg: save_request(msg, message.text))

def save_request(message: Message, ad_type):
    text = message.text.strip()
    if ad_type == "🎁 هدية NFT" and not text.startswith(("https://t.me/nft/", "http://t.me/nft/", "t.me/nft/")):
        bot.send_message(message.chat.id, "هذا القسم مخصص لهدايا NFT، يرجى إرسال رابط مثل: t.me/nft/SnoopCigar-2919", disable_web_page_preview=True)
        return
    elif ad_type in ["👤 يوزر NFT", "🏆 يوزر ملكية"] and not text.startswith("@"):
        bot.send_message(message.chat.id, "هذا القسم خاص باليوزرات، يرجى إرسال يوزر مثل: @ddddi")
        return
    cursor.execute("INSERT INTO requests (user_id, type, url, status) VALUES (?, ?, ?, 'pending')",
                   (message.from_user.id, ad_type, message.text))
    conn.commit()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{message.from_user.id}"))
    bot.send_message(ADMIN_ID, f"طلب جديد من @{message.from_user.username}\nالنوع: {ad_type}\nالرابط: {message.text}", reply_markup=markup)
    bot.send_message(message.chat.id, "تم إرسال طلبك للمراجعة.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_approval(call: CallbackQuery):
    if call.message.from_user.id != ADMIN_ID:
        return
    user_id = int(call.data.split('_')[1])
    cursor.execute("SELECT * FROM requests WHERE user_id = ? AND status = 'pending'", (user_id,))
    request = cursor.fetchone()
    if not request:
        bot.answer_callback_query(call.id, "لا يوجد طلب.")
        return
    if call.data.startswith("approve"):
        if request[2] == "🎁 هدية NFT":
            msg = f" Upgraded Gift Soom • ( [Details]({request[3]}) ) 🎁\n"
        elif request[2] == "👤 يوزر NFT":
            msg = f"NFT Username  • ( {request[3]} )👤\n"
        elif request[2] == "🏆 يوزر ملكية":
            msg = f"Ownership Username • ( {request[3]} )🏆\n"
        msg += "\n*يمنع الكلام داخل المناقشة - ممنوع دفع سعر وعدم الشراء اذا خالفت القوانين يتم حظرك من القناة*\n\n"
        msg += f"Auction channel - @{CHANNEL_USERNAME}"
        bot.send_message(CHANNEL_ID, msg, parse_mode='Markdown', disable_web_page_preview=True)
        bot.send_message(user_id, "تم نشر إعلانك بنجاح.")
    else:
        bot.send_message(user_id, "تم رفض إعلانك.")
    cursor.execute("DELETE FROM requests WHERE id = ?", (request[0],))
    conn.commit()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        cursor.execute("INSERT OR IGNORE INTO banned (user_id) VALUES (?)", (user_id,))
        conn.commit()
        bot.reply_to(message, f"تم حظر المستخدم {user_id}")
    except:
        bot.reply_to(message, "صيغة الأمر غير صحيحة. استخدم: /ban user_id")

@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        cursor.execute("DELETE FROM banned WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.reply_to(message, f"تم إلغاء الحظر عن المستخدم {user_id}")
    except:
        bot.reply_to(message, "صيغة الأمر غير صحيحة. استخدم: /unban user_id")

@bot.message_handler(commands=['stats'])
def stats(message: Message):
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM requests")
    requests = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM banned")
    banned = cursor.fetchone()[0]
    bot.reply_to(message, f"📊 الإحصائيات:\nعدد المستخدمين: {users}\nالطلبات الحالية: {requests}\nالمحظورين: {banned}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = message.text.split(' ', 1)
    if len(msg) < 2:
        bot.reply_to(message, "اكتب الرسالة بعد الأمر. مثل: /broadcast مرحباً بالجميع")
        return
    cursor.execute("SELECT id FROM users")
    for user in cursor.fetchall():
        try:
            bot.send_message(user[0], msg[1])
        except:
            pass
    bot.reply_to(message, "تم إرسال الرسالة لجميع المستخدمين.")


@bot.message_handler(commands=['admin'])
def broadcast(message:Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = """
• أهلا بك عزيزي المطور 😊: 
- هذي الاوامر المتاحة لك👇: 

- الاحصائيات :  /stats
- انشاء إذاعة  :  /broadcast
-حظر مستخدم بالايدي  : /ban
- الغاء حظر مستخدم بالايدي  :  /unban

• مطور السورس : @ddddi 🫶."""
    bot.send_message(chat_id=message.chat.id, text=text)
    return


if __name__ == "__main__":
    bot.send_message(chat_id=ADMIN_ID, text="تم تشغيل البوت بنجاح ✅.")
    bot.polling()