import datetime
import logging

import os

import azure.functions as func

import json
import requests


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    # 1. Airtable API to get onboarders
    # 2. Clean the list
    # 3. Send message via TextMagic from the Human Resources account.

    headers = {
        "Authorization": f"Bearer {os.environ['AIRTABLETOKEN']}"
    }

    url = "https://api.airtable.com/v0/appbkLLqkwnDd6gSy/Onboarding?view=Grid%20view"

    self = requests.get(url, headers=headers).json()
    print(self)