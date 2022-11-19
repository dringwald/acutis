import json
from datetime import datetime
from flask import Flask
from flask import request
from acutisapi import ynab
from acutisapi.notify import push

app = Flask(__name__)


@app.route("/")
def return_one():
    return "server active."

@app.route("/api")
def return_api_text():
    return "Cool"

@app.route("/ynab/to_allowance/<amount>")
def to_allowance(amount):
    amount = int(amount)
    r = ynab.move("daily_hold", "daily_free", amount)
    if r[0]:
        push(
            "Budget updated successfully",
            f"${amount} was added to your daily use budget.",
        )
        return "1"
    else:
        push(
            "Budget update failed!",
            f"There was a problem moving ${amount} into your daily use budget. Function returned {r[1]}",
        )
        return "0"


@app.route("/ynab/to_monk/<amount>")
def to_monk(amount):
    r = ynab.move("daily_free", "to_monk", int(amount), protected=False)
    if r[0]:
        push(
            f"You were late waking up!",
            f"${amount} was taken from your allowance to be given to Monk.",
        )
        return "1"
    else:
        push(
            f"Today's a bad morning.",
            "Not only were you late; there was a problem moving ${amount} into your daily use budget. Function returned {r[1]}",
        )
        return "0"

@app.route("/ynab/allowance")
def allowance():
    r = ynab.move_equal_allowance()
    return f"moved ${r}"

@app.route("/snitch", methods = ["GET","POST"])
def snitch():

    if request.method == 'GET':
        try:
            with open("postdata.txt","r") as f:
                return f'<pre>{f.read()}</pre>' 
        except FileNotFoundError:
            return "No data available"

    elif request.method == 'POST':
        state = get_state()

        if "snitch" not in state:
            snitch_disarm()

        if state["snitch"] == False:
            return "Snitching not armed."

        # If snitching is active, see if this is a valid
        elif request.headers['Content-Type'] == 'application/json':
            data = request.get_json().get(['bluetoothresults'],[])
            for item in data:
                if item['address'] == '1A:BF:ED:46:1C:E1':
                    if item['connected']:
                        # Turn off snitching
                        record = 'Request confirmed sent from car'
                        snitch_disarm()
                    else:
                        record = 'ERROR: Request NOT confirmed to be sent from car'
                else:
                    record = 'ERROR: Malformed data sent with request.'
        else:
            # Data is not json
            data = f"Invalid data sent: {request.data}"

        with open("postdata.txt","a") as f:
            now = datetime.now().ctime()
            f.write(f"{now} - {record}\n")

        # Save state before exiting
        return "OK"

    # Neither post nor get
    else:
        return "Something went wrong"

def snitch_fail():
    to_monk(5)

@app.route("/snitch/check")
def snitch_check():
    s = get_state
    if "snitch" in s and s['snitch'] is True:
        snitch_fail()


@app.route("/snitch/arm")
def snitch_arm():
    snitch_switch(True)
    return "1"

@app.route("/snitch/disarm")
def snitch_disarm():
    snitch_switch(False)
    return "0"

def snitch_switch(b):
    state = get_state() 
    state["snitch"] = b
    write_state(state)

def get_state():
    try:
        with open("state.json","r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open("state.json","w") as f:
            json.dump({},f)
            return {}

def write_state(state):
    with open("state.json","w") as f:
        json.dump(state,f)

if __name__ == "__main__":
    app.run()
