import json 
from pushover import Pushover

secrets = {"app_token":"a1c7f5g5pw2d7nxt1qb9bwcyesmped",
    "user_token":"u27psikhwywa2kba8a594zotexyvqs"}
_app_token = secrets["app_token"]
_user_token = secrets["user_token"]

po = Pushover(_app_token)
po.user(_user_token)

def push(title,message):
    msg = po.msg(message)
    msg.set("title",title)
    po.send(msg)

