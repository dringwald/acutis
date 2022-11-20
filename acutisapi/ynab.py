import json
import logging
import datetime
from datetime import timedelta
from requests.exceptions import HTTPError
import requests
from acutisapi.app import app

secrets = {
    "budget_id": "8f3d7058-c7b4-42ec-b42a-c9466fbe652f",
    "api_key": "r9RCtBKK66_587u-mwiqTpKUN9rxOf1Yeyt6OcTkDyM",
    "categories": {
        "daily_hold": "629cadbc-8742-4ce8-a223-afba26f96aa0",
        "daily_free": "b4d80503-e0ad-460e-8650-dff220462993",
        "to_monk": "8b5b2c86-7a89-471c-903f-2489e85d41d4",
    },
}

# updated with last result
RESULT = None
log = logging.getLogger("ynab")
plog = logging.getLogger("push")

_api_key = secrets["api_key"]
_budget_id = secrets["budget_id"]

categories = secrets["categories"]

_headers = {"Authorization": f"Bearer {_api_key}", "accept": "application/json"}
_dheaders = _headers | {"Content-Type": "application/json"}

URL = "https://api.youneedabudget.com/v1"


@app.route("/ynab/to_allowance/<amount>")
def to_allowance(amount):
    amount = int(amount)
    r = move("daily_hold", "daily_free", amount)
    if r[0]:
        return "1"
    else:
        return "0"


@app.route("/ynab/to_monk/<amount>")
def to_monk(amount):
    r = move("daily_free", "to_monk", int(amount), protected=False)
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
    r = move_equal_allowance()
    return f"moved ${r}"


def test():
    r = requests.get(f"{URL}/user", headers=_headers)
    return r.json()


def move_equal_allowance():
    anchor = datetime.date(2022, 11, 4)
    today = datetime.date.today()
    delta = (today - anchor).days
    shares = 14 - (delta % 14)
    pool = get_amount("daily_hold")
    to_move = round(pool / shares, 2)
    log.info(f"moving {shares} shares of ${pool}: sending {to_move} to daily allowance.")
    move("daily_hold", "daily_free", to_move)
    return to_move


def get_amount(category, month="current") -> int:
    category_id = categories[category]
    url = f"{URL}/budgets/{_budget_id}/months/{month}/categories/{category_id}"
    response = requests.get(
        url,
        headers=_headers,
    )
    response.raise_for_status()
    j = response.json()
    return int(j["data"]["category"]["budgeted"]) / 1000 


def add_to_category(category, req_amount_to_move, month="current") -> requests.Response:
    current_amount = get_amount(category, month)
    amount_to_move = int(req_amount_to_move)
    new_amount = current_amount + amount_to_move

    if new_amount < 0:
        new_amount = 0

    category_id = categories[category]
    data = json.dumps({"category": {"budgeted": new_amount * 1000}})
    url = f"{URL}/budgets/{_budget_id}/months/{month}/categories/{category_id}"
    r: requests.Response = requests.patch(
        url,
        data=data,
        headers=_dheaders,
    )

    amount_moved = new_amount - current_amount
    
    _add_metadata(r,{"requested_amount":req_amount_to_move,"amount_moved":amount_moved,"account":category,"month":month})
    return r


def subtract_from_category(category, amount, month="current") -> requests.Response:
    amount = amount * -1
    return add_to_category(category, amount, month)

def _add_metadata(response:requests.Response,data:dict) -> requests.Response:
    d:dict = response.json()
    d["metadata"] = data 

def get_metadata(response:requests.Response) -> dict:
    return response.json()

def move(origin, target, amount, month="current", protected=True) -> requests.Response:
    # remove from origin
    try:
        r : requests.Response = subtract_from_category(origin, amount, month)
        r.raise_for_status()
        # In case there wasn't enough funds in origin update the amount
        # But only if this is a protected transfer.
        # If unprotected, you might end up assigning money to the target
        # that doesn't exit
        if protected:
            amount = get_metadata(r)["amount_moved"] * -1
    except HTTPError as e:
        # if an error happened, stop everything
        plog.error(f"Error occoured pulling {amount} from {origin}: {e.response.text}")
        return False

    # If the first move was successful, go to the second
    try:
        r = add_to_category(target, amount, month)
        r.raise_for_status()
    except HTTPError as e:
        # If you failed to put the money in target, try to return it to origin
        try:
            r = add_to_category(origin, amount, month)
            r.raise_for_status()
        except HTTPError as e:
            plog.error(f"Error: I couldn't put {amount} in {target} and I can't return it to {origin}")
            return False
        else:
            plog.error(f"Error occoured putting {amount} into {target}: {e.response.text}")
            return False
    # If both moves were successful
    log.info(f"${amount} was moved from {origin} to {target}.")
    return True
