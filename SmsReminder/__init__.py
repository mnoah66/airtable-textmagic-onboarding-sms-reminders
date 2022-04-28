import logging

import os
import pytz

import azure.functions as func

import json
import requests

import datetime
from datetime import datetime as dt


def main(mytimer: func.TimerRequest) -> None:
    textmagic_headers = {
        'x-tm-key': os.getenv('TEXTMAGICTOKEN'),
        'Content-Type':'application/x-www-form-urlencoded',
        'x-tm-username':os.getenv('TEXTMAGICUSERNAME')
    }

    def phone_lookup(phone):
        lookup_url = f"https://rest.textmagic.com/api/v2/lookups/{phone}"
        r = requests.get(lookup_url, headers=textmagic_headers).json()
        return r['type'] == 'mobile' or r['type'] == 'voip'
        
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    summary_dict = {'records':[]}

    headers = {
    'Authorization': f"Bearer {os.getenv('AIRTABLETOKEN')}",
    'Content-Type':'application/json'
    }

    # They have to have an orientation date, so filterByFormula
    # and specify only the fields we want/need.  The fields are IDs so 
    # field name changes in Airtable UI have no impact.
    # The response, however, only gives field names.  If ther are name changes, 
    # the rest of the code needs to be reviewed, starting at line 53: i['fields']['OrientationDateStrUTC24Hr']
    url = (
        "https://api.airtable.com/v0/appBRzX7owY8jkWAz/tbls1J1Xju0ggrYHA?view=viwpjMFK4zZdoxkyQ"
        "&filterByFormula=NOT%28%7BOrientationDateStrUTC24Hr%7D%20%3D%20%27%27%29" 
        "&fields%5B%5D=fldaXdKpTdki8d6mS&fields%5B%5D=fldpgCKuNxswubztm&fields%5B%5D=fldyEM332rlLeeLTb"
        "&fields%5B%5D=fldYHHzyMl38ac6JH&fields%5B%5D=fldx92Wk3i9hPceOt"
        "&fields%5B%5D=fldlwppBEfTTcgQEV"
    )
    self=requests.get(url, headers=headers).json()
    records = self['records']
    
    if not records:
        headers = {
            'Content-Type': 'application/json'
        }
        summary_dict['records'].append({'name': f"na", 'cell':'na', 'msg': "Records were empty from Airtable response.  Either nobody is in onboarding or the view was deleted.", 'response':"na"})
        r = requests.post(os.getenv('SUMMARYWEBHOOK'), headers=headers, json=summary_dict)
        
    dt_now = dt.now(pytz.utc)
   
    textmagic_url = "https://rest.textmagic.com/api/v2/messages"

    for i in records:
        orientation_date = dt.strptime(i['fields']['OrientationDateStrUTC24Hr'][0], '%m/%d/%y %H:%M').replace(tzinfo=pytz.utc)
        first_name = i['fields']['First Name']
        last_name = i['fields']['Last Name']
        cell = i['fields']['PhoneSanitized'] 
        o_date = i['fields']['OrientationDateStringRegular'][0]
        o_date_obj = dt.strptime(o_date, "%m/%d/%Y %I:%M%p")
        o_date_friendly = dt.strftime(o_date_obj,  "%b %d, %Y at %I:%M %p")
        if orientation_date > dt_now:
            if not phone_lookup(cell):
                summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': "[ERROR]:  number is a landline.", 'response':"na"})
                continue # go to next person
            msg = f"Welcome to the Arc of Essex County, {first_name}! Just a friendly reminder that you are scheduled for pre-service training on {o_date_friendly}. For any questions, please reach out to the Onboarding Team at (973) 535-1182 ext. 1211 or 1256. "
            payload = {'phones':cell, 'text':msg}
            # Testing
            # summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':"Testing e.g. 201"})
            # Production
            r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
            summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")})
        else:
            if not phone_lookup(cell):
                summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': "[ERROR]: The number in Airtable is a landline.", 'response':"na"})
                continue # go to next person
            # Orientation date is in the past.  Check if the Onboarding Complete? checkbox is entered.
            # Airtable does not send this field if it is empty. So check if it's in fields with a try/except.
            try:
                oc = i['fields']['Onboarding Complete']
                msg = "NOTE: Onboarding is complete and pre-service date is in the past.  The employee should not be in the onboarding view.  Please change their Applicant Stage and/or Primepoint Status."
                summary_dict['records'].append({'name':f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response': 'na'})
            except:
                msg = f"Hello {first_name}, just a friendly reminder you still have outstanding onboarding tasks to complete with The Arc of Essex County before being released to program. For more information, please reach out to the Onboarding Team at (973) 535-1182 ext. 1211 or 1256."    
                payload = {'phones':cell, 'text':msg}
                # Testing
                #summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':"Testing e.g. 201"})
                # Production
                r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
                summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")})
    
    headers = {
        'Content-Type': 'application/json'
    }
    r = requests.post(os.getenv('SUMMARYWEBHOOK'), headers=headers, json=summary_dict)