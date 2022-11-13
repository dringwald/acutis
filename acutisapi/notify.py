import json 
from pushover import Pushover
with open("pushover_data.json") as f:
    secrets = json.load(f)
_app_token = secrets["app_token"]
_user_token = secrets["user_token"]

po = Pushover(_app_token)
po.user(_user_token)

def push(title,message):
    msg = po.msg(message)
    msg.set("title",title)
    po.send(msg)