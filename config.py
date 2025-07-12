from os import path, getenv

class Config:
    # توكن البوت
    BOT_TOKEN = getenv("BOT_TOKEN", "7134707061:AAGJ8McRWj1QhlxnB6WF7RBJEEcBNqZanAU")
    #يوزر قناة المزاد
    FSUB = getenv("FSUB", "mmmzm")
    # ايدي قناة المزاد 
    CHID = int(getenv("CHID", "-1002041113828"))
    # ايدي مالك المزاد 
    SUDO = int(getenv("CHID", "926877758"))
    # يوزر مالك المزاد
    ADMIN = getenv("ADMIN", "ddddi")
    # اسم المزاد
    NAME_AUCTION = getenv("NAME_AUCTION", "Auction Xx")
    
cfg = Config()