import logging

import os
import pytz

import azure.functions as func

import json
import requests

from helperfuncs.utils import tomorrow_testing_dates, tomorrow_fingerprint_date



import datetime
from datetime import datetime as dt
from dateutil import parser

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
    at_headers = {
        'Authorization': f"Bearer {os.getenv('AIRTABLETOKEN')}",
        'Content-Type':'application/json'
    }

    # filterByFormula = OR({drug test},{finger prints}, etc...)
    # if there is at least one value in any of those columns...
    url = (
        "https://api.airtable.com/v0/appBRzX7owY8jkWAz/tbls1J1Xju0ggrYHA?view=viwpjMFK4zZdoxkyQ"
        "&filterByFormula=OR(%7BFingerprints+scheduled+date%7D%2C+%7BTB+scheduled+date%7D%2C+%7BPhysical+scheduled+date%7D%2C+%7BDrug+test+scheduled+date%7D)" 
        "&fields=fldaXdKpTdki8d6mS&fields=fldpgCKuNxswubztm&fields=fldyEM332rlLeeLTb"
        "&fields=fldYHHzyMl38ac6JH&fields=fldx92Wk3i9hPceOt"
        "&fields=fldlwppBEfTTcgQEV"
        "&fields=fldqXNNK6ZFUgQOOa"
        "&fields=fldyREPLZ8tBgbDla" # Drug Test Scheduled Date
        "&fields=fldxg9F52XGvqnt7V" # Physical scheduled date
        "&fields=fld8xJxvnWX1aM9Nb" # TB Scheduled Date
        "&fields=fldbo8yWhA0gCTZMM" # Fingerprints Scheduled Date
    )
    self=requests.get(url, headers=at_headers).json()
    records = self['records']
    
    if not records:
        headers = {
            'Content-Type': 'application/json'
        }
        summary_dict['records'].append({'name': f"na", 'cell':'na', 'msg': "Records were empty from Airtable response.  Either nobody is in onboarding or the view was deleted.", 'response':"na"})
        r = requests.post(os.getenv('SUMMARYWEBHOOK'), headers=headers, json=summary_dict)
        

    textmagic_url = "https://rest.textmagic.com/api/v2/messages"
    for item in records:
        first_name = item['fields']['First Name']
        last_name = item['fields']['Last Name']  
        cell = item['fields']['PhoneSanitized'] 
        
        # Check if any testing dates tomorrow
        if tomorrow_testing_dates(item):
            if not phone_lookup(cell):
                summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': "[ERROR]:  number is a landline.", 'response':"na"})
                continue # go to next person
            msg = f"Welcome to the Arc of Essex County, {item['fields']['First Name']}! Just a friendly reminder that you are scheduled pre-employment testing at City MD tomorrow. For any questions, please reach out to the Onboarding Team at (973) 535-1181 ext. 1211 or 1256."
            payload = {'phones':cell, 'text':msg}
            # Testing
            # summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':"Testing e.g. 201"})
            # Production
            r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
            summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")})
        
        # Check if fingerprint is tomorrow
        if tomorrow_fingerprint_date(item):
            if not phone_lookup(cell):
                summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': "[ERROR]:  number is a landline.", 'response':"na"})
                continue # go to next person
            msg = f"Welcome to the Arc of Essex County, {item['fields']['First Name']}! Just a friendly reminder that you are scheduled fingerprinting at IdentoGO tomorrow, {item['fields']['FingerprintDateString']}. For any questions, please reach out to the Onboarding Team at (973) 535-1181 ext. 1211 or 1256."
            payload = {'phones':cell, 'text':msg}
            # Testing
            # summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':"Testing e.g. 201"})
            # Production
            r = requests.post(textmagic_url, headers=textmagic_headers, data=payload)
            summary_dict['records'].append({'name': f"{last_name}, {first_name}", 'cell':cell, 'msg': msg, 'response':str(f"{r.status_code}: {r.text}")})
    
    power_automate_headers = {
        'Content-Type': 'application/json'
    }
    r = requests.post(os.getenv('SUMMARYWEBHOOK'), headers=power_automate_headers, json=summary_dict)