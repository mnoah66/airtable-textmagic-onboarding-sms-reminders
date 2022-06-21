import logging
import azure.functions as func


from datetime import datetime
import json
import pytz
import os

import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    return func.HttpResponse(
            f"get outta here",
            status_code=200
    )
