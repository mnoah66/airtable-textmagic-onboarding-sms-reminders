import datetime
import logging

import os
import pytz

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
        'Authorization':os.getenv('AIRTABLETOKEN'),
        'Content-Type':'application/json'
    }

    # They have to have an orientation date, so filterByFormula
    url = "https://api.airtable.com/v0/appbkLLqkwnDd6gSy/Onboarding?view=Grid%20view&filterByFormula=NOT%28%7BOrientationDateStrUTC24Hr%7D%20%3D%20%27%27%29"
    self=requests.get(url, headers=headers).json()
    records = self['records']
    
    newyork_tz = pytz.timezone('America/New_York')
    dt_now = datetime.datetime.now(pytz.utc)
    

    for i in records:
        orientation_date = datetime.datetime.strptime(i['fields']['OrientationDateStrUTC24Hr'][0], '%m/%d/%y %H:%M').replace(tzinfo=pytz.utc)
        print("orientation_date: ", orientation_date,", dt_now: ", dt_now)
        first_name = i['fields']['First Name']
        last_name = i['fields']['Last Name']
        cell = i['fields']['CellSanitized'] 
        o_date = i['fields']['DateStringRegular (from Orientation)'][0]
        o_date_obj = datetime.datetime.strptime(o_date, "%m/%d/%Y %I:%M%p")
        o_date_friendly = datetime.datetime.strftime(o_date_obj,  "%b %d, %Y at %I:%M %p")
        if orientation_date > dt_now:
            print(True)