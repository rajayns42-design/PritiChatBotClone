from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_ID = "25609334"
# -------------------------------------------------------------
API_HASH = "ad0ff353206ea1ebce1ab8bfca9f3f7b"
# --------------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING1 = getenv("STRING_SESSION", None)
MONGO_URL = getenv("MONGO_URL", None)
OWNER_ID = int(getenv("OWNER_ID", "8217013403"))
SUPPORT_GRP = "LuckyXSupport"
UPDATE_CHNL = "Luckyxupdate"
OWNER_USERNAME = "The_LuckyX"
LOGGER_GROUP = -1003213095654
