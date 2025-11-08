import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env (إذا كان موجودًا)
load_dotenv()

class Config:
    # المتغيرات الأساسية المطلوبة
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    FSUB = os.getenv("FSUB")
    CHID = os.getenv("CHID")
    SUDO = os.getenv("SUDO")
    ADMIN = os.getenv("ADMIN")
    NAME_AUCTION = os.getenv("NAME_AUCTION")
    CHID2 = os.getenv("CHID2")

    # تحقق من المتغيرات الأساسية
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "FSUB": FSUB,
        "CHID": CHID,
        "SUDO": SUDO,
        "ADMIN": ADMIN,
        "NAME_AUCTION": NAME_AUCTION,
        "CHID2": CHID2
    }

    for var_name, value in required_vars.items():
        if value is None or value.strip() == "":
            raise ValueError(f"⚠️ Environment variable '{var_name}' is missing or empty!")

    # تحويل بعض القيم إلى النوع الصحيح
    CHID = int(CHID)
    SUDO = int(SUDO)
    CHID2 = int(CHID2)

# إنشاء نسخة للوصول السريع
cfg = Config()

