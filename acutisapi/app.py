from flask import Flask
from acutisapi import ynab
from acutisapi.notify import push

app = Flask(__name__)


@app.route("/")
def return_one():
    return "server active."


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
    r = ynab.move("daily_free", "to_monk", amount)
    if r[0]:
        push(
            f"You were late waking up!",
            f"${amount} was taken from your allowance to be given to Monk.",
        )
    else:
        push(
            f"Today's a bad morning.",
            "Not only were you late; there was a problem moving ${amount} into your daily use budget. Function returned {r[1]}",
        )
