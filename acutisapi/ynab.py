import json
from urllib.error import HTTPError
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

with open("ynab_data.json") as f:
    secrets = json.load(f)
_api_key = secrets["api_key"]
_budget_id = secrets["budget_id"]

categories = secrets["categories"]

_headers = {"Authorization": f"Bearer {_api_key}", "accept": "application/json"}
_dheaders = _headers | {"Content-Type": "application/json"}

URL = "https://api.youneedabudget.com/v1"


def test():
    r = requests.get(f"{URL}/user", headers=_headers)
    return r.json()


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
    current_amount = get_amount(category, month)
    amount_to_move = amount_to_move * 1000
    new_amount = current_amount + amount_to_move
    if new_amount < 0:
        moved_amount = current_amount / 1000
        new_amount = 0
    else:
        moved_amount = amount_to_move / 1000
    category_id = categories[category]
    data = json.dumps({"category": {"budgeted": new_amount}})
    url = f"{URL}/budgets/{_budget_id}/months/{month}/categories/{category_id}"
    print("########################################")
    r: requests.Response = requests.patch(
        url,
        data=data,
        headers=_dheaders,
    )
    return {"amound_moved": moved_amount, "response": r}


def subtract_from_category(category, amount, month="current"):
    if amount >= 0:
        amount = amount * -1
    return (add_to_category(category, amount, month), amount)


def move(origin, target, amount, month="current"):
    # remove from origin
    try:
        r = subtract_from_category(origin, amount, month)
        r["response"].raise_for_status()
        # In case there wasn't enough funds in origin update the amount
        amount = r["amount_moved"]
    except HTTPError:
        # if an error happened, stop everything
        return (False, f"Error in removing allowance from {target}.", r)
    else:
        # If the first move was successful, go to the second
        try:
            r = add_to_category(target, amount, month)
            r["response"].raise_for_status()
        except HTTPError:
            try:
                r = add_to_category(origin, amount, month)
                r["response"].raise_for_status()
            except HTTPError:
                return (
                    False,
                    f"Couldn't add money to {target} Couldn't return money to {origin}",
                    r,
                )
            else:
                return (
                    False,
                    f"Couldn't add money to {target}. Money returned to {origin}",
                    r,
                )
    return (True, "Task completed successfully")
