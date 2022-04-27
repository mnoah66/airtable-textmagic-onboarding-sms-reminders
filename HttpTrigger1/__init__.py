import logging
from zoneinfo import ZoneInfo
import azure.functions as func


from datetime import datetime
import json
import pytz
import os

import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    headers = {
    'Authorization':os.getenv('AIRTABLETOKEN'),
    'Content-Type':'application/json'
    }

    # They have to have an orientation date, so filterByFormula
    url = "https://api.airtable.com/v0/appbkLLqkwnDd6gSy/Onboarding?view=Grid%20view&filterByFormula=NOT%28%7BOrientationDateStrUTC24Hr%7D%20%3D%20%27%27%29"
    self=requests.get(url, headers=headers).json()
    records = self['records']
    
    newyork_tz = pytz.timezone('America/New_York')
    dt_now = datetime.now(pytz.utc)

    textmagic_headers = {
                'x-tm-key': os.getenv('TEXTMAGICTOKEN'),
                'Content-Type':'application/x-www-form-urlencoded',
                'x-tm-username':'martinnoah'
            }
    textmagic_url = "https://rest.textmagic.com/api/v2/messages"

    summary_dict = {}
    for i in records:
        orientation_date = datetime.strptime(i['fields']['OrientationDateStrUTC24Hr'][0], '%m/%d/%y %H:%M').replace(tzinfo=pytz.utc)
        print("orientation_date: ", orientation_date,", dt_now: ", dt_now)
        first_name = i['fields']['First Name']
        last_name = i['fields']['Last Name']
        cell = i['fields']['CellSanitized'] 
        o_date = i['fields']['DateStringRegular (from Orientation)'][0]
        o_date_obj = datetime.strptime(o_date, "%m/%d/%Y %I:%M%p")
        o_date_friendly = datetime.strftime(o_date_obj,  "%b %d, %Y at %I:%M %p")
        if orientation_date > dt_now:
            msg = f"Welcome to the Arc of Essex County, {first_name}! Just a friendly reminder that you are scheduled for pre-service training on {o_date_friendly}. For any questions, please reach out to the Onboarding Team at (973) 535-1182 ext. 1211 or 1256. "
            payload = {'phones':cell, 'text':msg}
            r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
            summary_dict[f"{last_name}, {first_name}"] = {'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")}
        else:
            # Orientation date is in the past.  Check if the Onboarding Complete? checkbox is entered.
            # Airtable does not send this field if it is empty. So check if it's in fields with a try/except.
            try:
                oc = i['fields']['Onboarding Complete?']
                msg = "NOTE: Onboarding is complete and pre-service date is in the past.  The employee should not be in the onboarding view.  Please change their Applicant Stage and/or Primepoint Status."
                summary_dict[f"{last_name}, {first_name}"] = {'cell':cell, 'msg': msg, 'response': 'Not applicable'}
            except:
                msg = f"Hello {first_name}, just a friendly reminder you still have outstanding onboarding tasks to complete with The Arc of Essex County before being released to program. For more information, please reach out to the Onboarding Team at (973) 535-1182 ext. 1211 or 1256."    
                payload = {'phones':cell, 'text':msg}
                r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
                summary_dict[f"{last_name}, {first_name}"] = {'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")}
    
    print(summary_dict)
    headers = {
        'Content-Type': 'application/json'
    }
    r = requests.post(os.getenv('SUMMARYWEBHOOK'), headers=headers, json=summary_dict)
    print(r.text)
    return func.HttpResponse(
            f"{msg}",
            status_code=200
    )
