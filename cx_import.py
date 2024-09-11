import cx_infra
from os import environ
import json
import argparse
import re

if __name__ == '__main__':

    # Required api_key for enrichment
    cx_api_key = environ.get('CX_API_KEY')
    cx_api_key_region = environ.get('CX_API_KEY_REGION')

    parser = argparse.ArgumentParser()
    parser.add_argument('--alert_name', dest='alert_name', type=str, help="add alert name")
    parser.add_argument('--alert_file_name', dest='file_name', type=str, help="add file name")
    args = parser.parse_args()
    if args.alert_name and args.file_name:
        alerts_file = open(args.file_name)
        alerts = json.load(alerts_file)
        for alert in alerts["alerts"]:
            if re.search(args.alert_name, alert["name"]):
                cx_infra.create_alert(cx_api_key_region, cx_api_key, alert)
