import telebot
from telebot import types
import sqlite3
from config import cfg
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton 
import threading
import time
import logging

# --------------------- إعداد logging ---------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = cfg.BOT_TOKEN
ADMIN_ID = cfg.SUDO
CHANNEL_ID = cfg.CHID
CHANNEL_USERNAME = cfg.FSUB
NAME_AUCTION = cfg.NAME_AUCTION
ADMIN = cfg.ADMIN

bot = telebot.TeleBot(API_TOKEN, parse_mode='Markdown ')

# --------------------- إعداد قاعدة البيانات ---------------------
DB_PATH = 'nft_bot.db'
DB_TIMEOUT = 30
db_lock = threading.Lock()


def init_db():
    """تهيئة قاعدة البيانات وتفعيل WAL"""
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False)
    try:
        cur = conn.cursor()
        cur.execute('PRAGMA journal_mode=WAL;')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, url TEXT, status TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)''')
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_conn():
    """فتح اتصال جديد لكل عملية (آمن للثريدات)."""
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
    except Exception:
        pass
    return conn


# --------------------- وظائف مساعدة ---------------------
escape_chars = r"_*[]()~`>#+-=|{}.!\\"
def escape_markdown_v2(text: str) -> str:
    """هروب أحرف MarkdownV2"""
    if not text:
        return ''
    return ''.join(['\\' + ch if ch in escape_chars else ch for ch in text])


def is_banned(user_id: int) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM banned WHERE user_id = ?", (user_id,))
        return cur.fetchone() is not None
    finally:
        cur.close()
        conn.close()


def add_user(user):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user.id, user.username))
        conn.commit()
    finally:
        cur.close()
        conn.close()


# --------------------- handlers ---------------------
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
    text = f"👋🏻|مرحباً بك،{escape_markdown_v2(message.from_user.full_name)}\n\nيمكنك المشاركة في المزاد عن طريق الضغط على 'نشر مزاد' من الأسفل والانضمام إلى المجموعة. نحن في انتظار مساهماتك ومشاركتك في المزاد!"
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "AFC")
def handle_ASC(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("رجوع .", callback_data="cancel"))

    text = (
        "~ نوافق على المُعرفات المرتبة ✓.\n\n"
        "- يكون المعرف على قناة فارغة مابيها معرف تواصل فقط معرف قناة المزاد مِثال - ( المزاد هنا @mmmzm ).\n\n"
        "- ارسل مُعرفك الى الزر الخاص به ( ملكية - NFT - مقتنى ).\n"
        "- الهدية يجب ان تكون في حسابك حصرا.\n\n"
        "- عدم تضمين اي طريقة للتواصل في داخل قناة المعرف. \n\n"
        "- اذا يوجد مزاد ثاني في قناة المعرف ما ينشر مُعرفك.\n\n"
        "- لبدء نشر مزادك اضغط 'نشر مزاد' واختر نوع المزاد وارسل الرابط إذا كان مقتنى رقمي، ومعرف اذا كان يوزر.\n"
        f"Channel : @{CHANNEL_USERNAME}\nOwner : @{ADMIN}"
    )

    try:
        bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.id,
            reply_markup=markup
        )
    except Exception as e:
        logging.exception('edit_message_text AFC failed')


@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("شروط النشر  .", callback_data="AFC"),
               InlineKeyboardButton("نشر مزاد .", callback_data="Great_ads"))
    markup.add(InlineKeyboardButton(f"{NAME_AUCTION}", url=f"https://t.me/{CHANNEL_USERNAME}"))
    text = f"👋🏻|مرحباً بك،{escape_markdown_v2(call.from_user.full_name)}\n\nيمكنك المشاركة في المزاد عن طريق الضغط على 'نشر مزاد' من الأسفل والانضمام إلى المجموعة. نحن في انتظار مساهماتك ومشاركتك في المزاد!"
    try:
        bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.exception('edit_message_text cancel failed')


@bot.callback_query_handler(func=lambda call: call.data == "Great_ads")
def handle_Great_ads(call: CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎁 هدية NFT", callback_data="type_gift"))
    markup.add(types.InlineKeyboardButton("👤 يوزر NFT", callback_data="type_user_nft"),
               types.InlineKeyboardButton("🏆 يوزر ملكية", callback_data="type_user_premium"))
    markup.add(types.InlineKeyboardButton("رجوع .", callback_data="cancel"))
    text = "- أختار نوع الاعلان : "
    try:
        bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.exception('edit_message_text Great_ads failed')


@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type_selection(call: CallbackQuery):
    ad_type = {
        "type_gift": "🎁 هدية NFT",
        "type_user_nft": "👤 يوزر NFT",
        "type_user_premium": "🏆 يوزر ملكية"
    }.get(call.data, "غير معروف")
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"أرسل رابط {ad_type}:")
    bot.register_next_step_handler(call.message, lambda msg: save_request(msg, ad_type))


@bot.message_handler(func=lambda message: message.text in ["🎁 هدية NFT", "👤 يوزر NFT", "🏆 يوزر ملكية"])
def request_url(message):
    bot.send_message(message.chat.id, "أرسل رابط الهدية أو القناة:")
    bot.register_next_step_handler(message, lambda msg: save_request(msg, message.text))


def save_request(message: Message, ad_type: str):
    # حماية قصيرة ضد التنافس باستخدام قفل (اختياري)
    # with db_lock:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM requests WHERE user_id = ? AND status = 'pending'", (message.from_user.id,))
        if cur.fetchone():
            bot.send_message(message.chat.id, "🚫 لديك إعلان قيد المراجعة بالفعل. يرجى الانتظار حتى يتم قبوله أو رفضه قبل إرسال إعلان جديد.")
            return

        text = (message.text or '').strip()
        if ad_type == "🎁 هدية NFT" and not text.startswith(("https://t.me/nft/", "http://t.me/nft/", "t.me/nft/")):
            bot.send_message(message.chat.id, "هذا القسم مخصص لهدايا NFT، يرجى إرسال رابط مثل: t.me/nft/SnoopCigar-2919", disable_web_page_preview=True)
            return
        elif ad_type in ["👤 يوزر NFT", "🏆 يوزر ملكية"] and not text.startswith("@"):
            bot.send_message(message.chat.id, "هذا القسم خاص باليوزرات، يرجى إرسال يوزر مثل: @ddddi")
            return

        cur.execute("INSERT INTO requests (user_id, type, url, status) VALUES (?, ?, ?, 'pending')",
                    (message.from_user.id, ad_type, text))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    username = message.from_user.username
    if username:
        user_tag = f"@{escape_markdown_v2(username)}"
    else:
        user_tag = f"[{escape_markdown_v2(message.from_user.first_name)}](tg://user?id={message.from_user.id})"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{message.from_user.id}"))

    msg = (
        f"طلب جديد من {user_tag}\n"
        f"النوع: {escape_markdown_v2(ad_type)}\n"
        f"الرابط: {escape_markdown_v2(text)}"
    )
    try:
        bot.send_message(cfg.CHID2, msg, reply_markup=markup, parse_mode='MarkdownV2')
    except Exception:
        logging.exception('send to admin channel failed')

    bot.send_message(message.chat.id, "تم إرسال طلبك للمراجعة.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_approval(call: CallbackQuery):
    user_id = int(call.data.split('_')[1])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM requests WHERE user_id = ? AND status = 'pending'", (user_id,))
        request = cur.fetchone()
        if not request:
            bot.answer_callback_query(call.id, "لا يوجد طلب.")
            return

        if call.data.startswith("approve"):
            if request[2] == "🎁 هدية NFT":
                link = escape_markdown_v2(request[3])
                msg = f"Upgraded Gift Soom • [Details]({link}) 🎁\n"
            elif request[2] == "👤 يوزر NFT":
                username = escape_markdown_v2(request[3])
                msg = f"NFT Username • {username} 👤\n"
            elif request[2] == "🏆 يوزر ملكية":
                username = escape_markdown_v2(request[3])
                msg = f"Ownership Username • {username} 🏆\n"
            else:
                fallback = escape_markdown_v2(request[3])
                msg = f"🔹 إعلان جديد • ( [Details]({fallback}))\n"
            rules_text = "يمنع الكلام داخل المناقشة - ممنوع دفع سعر وعدم الشراء اذا خالفت القوانين يتم حظرك من القناة."
            msg += escape_markdown_v2(rules_text) + "\n\n"
            ttt = f"Auction channel - @{CHANNEL_USERNAME}"
            msg += escape_markdown_v2(ttt)
            try:
                send = bot.send_message(CHANNEL_ID, msg, parse_mode='MarkdownV2', disable_web_page_preview=False)
                message_id = send.message_id
                link_send = f"https://t.me/{CHANNEL_USERNAME}/{message_id}"
                bot.send_message(user_id, "تم نشر إعلانك بنجاح.\n {}".format(link_send), disable_web_page_preview=True)
            except Exception:
                logging.exception('publish to channel failed')
                bot.send_message(user_id, "حصل خطأ أثناء نشر إعلانك. سيتم التواصل معك لاحقاً.")
        else:
            bot.send_message(user_id, "تم رفض إعلانك.")
        cur.execute("DELETE FROM requests WHERE id = ?", (request[0],))
        conn.commit()
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
    finally:
        cur.close()
        conn.close()


# --------------------- أوامر الإدارة ---------------------
@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO banned (user_id) VALUES (?)", (user_id,))
            conn.commit()
        finally:
            cur.close(); conn.close()
        bot.reply_to(message, f"تم حظر المستخدم {user_id}")
    except Exception:
        bot.reply_to(message, "صيغة الأمر غير صحيحة. استخدم: /ban user_id")


@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM banned WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            cur.close(); conn.close()
        bot.reply_to(message, f"تم إلغاء الحظر عن المستخدم {user_id}")
    except Exception:
        bot.reply_to(message, "صيغة الأمر غير صحيحة. استخدم: /unban user_id")


@bot.message_handler(commands=['stats'])
def stats(message: Message):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM requests")
        requests = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM banned")
        banned = cur.fetchone()[0]
        bot.reply_to(message, f"📊 الإحصائيات:\nعدد المستخدمين: {users}\nالطلبات الحالية: {requests}\nالمحظورين: {banned}")
    finally:
        cur.close(); conn.close()


@bot.message_handler(commands=['broadcast'])
def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = message.text.split(' ', 1)
    if len(msg) < 2:
        bot.reply_to(message, "اكتب الرسالة بعد الأمر. مثل: /broadcast مرحباً بالجميع")
        return
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users")
        users = cur.fetchall()
    finally:
        cur.close(); conn.close()

    sent = 0
    for user in users:
        try:
            bot.send_message(user[0], msg[1])
            sent += 1
        except Exception:
            logging.exception('broadcast send failed')
        time.sleep(0.08)

    bot.reply_to(message, f"تم إرسال الرسالة لـ {sent} مستخدمين.")


@bot.message_handler(commands=['admin'])
def admin_panel(message:Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = """
• أهلا بك عزيزي المطور 😊: 
- هذي الاوامر المتاحة لك👇: 

- الاحصائيات :  /stats
- انشاء إذاعة  :  /broadcast
-حظر مستخدم بالايدي  : /ban
- الغاء حظر مستخدم بالايدي  :  /unban
- حذف جميع الطلبات المعلقة : /clear

• مطور السورس : @ddddi 🫶.
"""
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['clear'])
def clear_pending(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM requests WHERE status = 'pending'")
        conn.commit()
    finally:
        cur.close(); conn.close()
    bot.reply_to(message, "✅ تم حذف جميع الطلبات المعلقة بنجاح.")


# --------------------- بدء التشغيل ---------------------
if __name__ == "__main__":
    init_db()
    try:
        bot.send_message(chat_id=ADMIN_ID, text="تم تشغيل البوت بنجاح ✅.")
    except Exception:
        logging.exception('could not notify admin at startup')
    bot.infinity_polling()
