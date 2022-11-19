import json
import datetime
from datetime import timedelta
from requests.exceptions import HTTPError
import requests

"""
## for advanced logging
import logging
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
"""

secrets = {
    "budget_id": "8f3d7058-c7b4-42ec-b42a-c9466fbe652f",
    "api_key": "r9RCtBKK66_587u-mwiqTpKUN9rxOf1Yeyt6OcTkDyM",
    "categories":{
        "daily_hold": "629cadbc-8742-4ce8-a223-afba26f96aa0",
        "daily_free": "b4d80503-e0ad-460e-8650-dff220462993",
        "to_monk": "8b5b2c86-7a89-471c-903f-2489e85d41d4"
        }
    }

_api_key = secrets["api_key"]
_budget_id = secrets["budget_id"]

categories = secrets["categories"]

_headers = {"Authorization": f"Bearer {_api_key}", "accept": "application/json"}
_dheaders = _headers | {"Content-Type": "application/json"}

URL = "https://api.youneedabudget.com/v1"


def test():
    r = requests.get(f"{URL}/user", headers=_headers)
    return r.json()


def move_equal_allowance():
    anchor = datetime.date(2022,11,4)
    today = datetime.date.today()
    delta = (today - anchor).days
    shares = 14 - (delta % 14)
    pool = get_amount('daily_hold') / 1000
    to_move = round(pool / shares,2)
    print(f'moving {shares} shares of ${pool}: sending {to_move} to daily allowance.')
    move('daily_hold','daily_free',to_move)
    return to_move

def get_amount(category, month="current"):
    category_id = categories[category]
    url = f"{URL}/budgets/{_budget_id}/months/{month}/categories/{category_id}"
    response = requests.get(
        url,
        headers=_headers,
    )
    response.raise_for_status()
    j = response.json()
    return j["data"]["category"]["budgeted"]


def add_to_category(category, amount_to_move, month="current"):
    current_amount = int(get_amount(category, month))
    amount_to_move = int(amount_to_move) * 1000
    new_amount = int(current_amount + amount_to_move)

    if new_amount < 0:
        moved_amount = current_amount / 1000
        new_amount = 0
    else:
        moved_amount = amount_to_move / 1000

    category_id = categories[category]
    data = json.dumps({"category": {"budgeted": new_amount}})
    url = f"{URL}/budgets/{_budget_id}/months/{month}/categories/{category_id}"
    r: requests.Response = requests.patch(
        url,
        data=data,
        headers=_dheaders,
    )
    return {"amount_moved": moved_amount, "response": r}


def subtract_from_category(category, amount, month="current"):
    amount = amount * -1
    return add_to_category(category, amount, month)


def move(origin, target, amount, month="current",protected=True):

    # remove from origin
    try:
        r = subtract_from_category(origin, amount, month)
        r["response"].raise_for_status()
        # In case there wasn't enough funds in origin update the amount
        # But only if this is a protected transfer.
        # If unprotected, you might end up assigning money to the target
        # that doesn't exit
        if protected:
            amount = r["amount_moved"] * -1
            print(f'{amount} FOO')
    except HTTPError as e:
        # if an error happened, stop everything
        print(e.text) 
        return (False, f"Error in removing allowance from {target}.", r)

    # If the first move was successful, go to the second
    try:
        r = add_to_category(target, amount, month)
        r["response"].raise_for_status()
    except HTTPError as e:
        print(e.text) 
        # If you failed to put the money in target, try to return it to origin
        try:
            r = add_to_category(origin, amount, month)
            r["response"].raise_for_status()
        except HTTPError as e:
            print(e.text) 
            return (
                False,
                f"Couldn't add money to {target}. Couldn't return money to {origin}",
                r,
            )
        else:
            return (
                False,
                f"Couldn't add money to {target}. Money returned to {origin}",
                r,
            )

    # If both moves were successful
    return (True, "Task completed successfully",r)

