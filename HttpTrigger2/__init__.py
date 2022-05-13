import logging, os

import azure.functions as func
import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    headers = {
        'Authorization': f"Bearer {os.getenv('AIRTABLETOKEN')}",
        'Content-Type':'application/json'
    }

    # They have to have a fingerprint date, so filterByFormula
    # and specify only the fields we want/need.  The fields are IDs so 
    # field name changes in Airtable UI have no impact.
    # The response, however, only gives field names.  If there **are** name changes, 
    # it won't impact the URL but the rest of the logic needs to be reviewed
    
    url = (
        "https://api.airtable.com/v0/appBRzX7owY8jkWAz/tbls1J1Xju0ggrYHA?view=viwpjMFK4zZdoxkyQ"
        "&filterByFormula=NOT(%7BFingerprints+scheduled+date%7D%3D'')" 
        "&fields=fldaXdKpTdki8d6mS&fields=fldpgCKuNxswubztm&fields=fldyEM332rlLeeLTb"
        "&fields=fldYHHzyMl38ac6JH&fields=fldx92Wk3i9hPceOt"
        "&fields=fldlwppBEfTTcgQEV"
        "&fields=fldbo8yWhA0gCTZMM"
    )
    
    self=requests.get(url, headers=headers).json()
    #records = self['records']

    logging.info(self)

    return func.HttpResponse(f"This HTTP triggered function executed successfully.")
   