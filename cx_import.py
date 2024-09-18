import cx_infra
from os import environ
import json
import argparse
import re


def import_alerts(alert_name, alerts_file):

    import_file = open(alerts_file)
    alerts = json.load(import_file)
    for alert in alerts["alerts"]:
        if re.search(alert_name, alert["name"]):
            cx_infra.create_alert(cx_api_key_region, cx_api_key, alert)


def import_grafana_dashboards(dashboard_name, dashboards_file):
    import_file = open(dashboards_file)
    dashboards = json.load(import_file)
    for dashboard in dashboards:
        if re.search(dashboard_name, dashboard["name"]):
            print(dashboard["dashboard_file_name"])


def import_cx_dashboards(dashboard_name, dashboards_file):
    import_file = open(dashboards_file)
    dashboards = json.load(import_file)
    for dashboard in dashboards:
        if re.search(dashboard_name, dashboard["name"]):
            print(dashboard["dashboard_file_name"])


if __name__ == '__main__':

    # Required api_key for enrichment
    cx_api_key = environ.get('CX_API_KEY')
    cx_api_key_region = environ.get('CX_API_KEY_REGION')

    parser = argparse.ArgumentParser()
    parser.add_argument('--alert_name', dest='alert_name', type=str, help="add alert name")
    parser.add_argument('--alert_file_name', dest='file_name', type=str, help="add file name")
    parser.add_argument('--grafana_dashboard', dest='grafana_dashboard', type=str, help="add grafana_dashboard")
    parser.add_argument('--grafana_file_name', dest='grafana_file_name', type=str, help="add grafana file name")
    parser.add_argument('--cx_dashboard', dest='cx_dashboard', type=str, help="add cx_dashboard")
    parser.add_argument('--cx_file_name', dest='cx_file_name', type=str, help="add cx file name")
    args = parser.parse_args()
    if args.alert_name and args.file_name:
        import_alerts(args.alert_name, args.file_name)

    if args.grafana_dashboard and args.grafana_file_name:
        import_grafana_dashboards(args.grafana_dashboard, args.grafana_file_name)

    if args.cx_dashboard and args.cx_file_name:
        import_cx_dashboards(args.cx_dashboard, args.cx_file_name)