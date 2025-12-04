from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_ID = ""
# -------------------------------------------------------------
API_HASH = ""
# --------------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING1 = getenv("STRING_SESSION", None)
MONGO_URL = getenv("MONGO_URL", None)
OWNER_ID = int(getenv("OWNER_ID", ""))
SUPPORT_GRP = "LuckyXSupport"
UPDATE_CHNL = "Luckyxupdate"
OWNER_USERNAME = "The_LuckyX"
