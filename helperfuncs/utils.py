import datetime
from dateutil import parser

def tomorrow_testing_dates(item):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    dates_arr = []
    try:
        physical_date_string = item['fields']['Physical scheduled date']
        dates_arr.append(physical_date_string)
    except:
        pass
    try:
        tb_date_string = item['fields']['TB scheduled date']
        dates_arr.append(tb_date_string)
    except:
        pass
    try:
        drug_date_string = item['fields']['Drug test scheduled date']
        dates_arr.append(drug_date_string)
    except:
        pass
    
    if dates_arr:
        for test_date in dates_arr:
            if parser.parse(test_date).date() == tomorrow:
                return True
            return False
    return False

def tomorrow_fingerprint_date(item):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    try:
        fingerprint_date = item['fields']['Fingerprints scheduled date']
        return parser.parse(fingerprint_date).date() == tomorrow
    except:
        return False