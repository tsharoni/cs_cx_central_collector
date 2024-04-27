
import json
from os import environ

import cx_central

if __name__ == '__main__':

    #cx_central.set_simulate()

    f = open('teams.json')
    teams_json = json.load(f)

    account_env = environ.get('account')
    for account in teams_json:
        if account_env != account["account"] and account_env != 'all':
            continue

        if "skip" in account and account["skip"]:
            continue

        print("\naccount: {}".format(account["account"]))

        for team in account["teams"]:
            cx_central.set_attributes(account["account"], team["name"])
            print("team: {}".format(team["name"]))
            cx_central.flush_alerts(region=team["region"], key=team["key"])
            cx_central.flush_webhooks(region=team["region"], key=team["key"])
            cx_central.flush_rules(region=team["region"], key=team["key"])
            cx_central.flush_tco_overrides(region=team["region"], key=team["key"])
            cx_central.flush_grafana(region=team["region"], key=team["key"])
            cx_central.flush_e2m(region=team["region"], key=team["key"])
            cx_central.flush_tco(region=team["region"], key=team["key"])
            cx_central.flush_recording_rule(region=team["region"], key=team["key"])
            cx_central.flush_apm_services(region=team["region"], key=team["key"])
            cx_central.flush_slo(region=team["region"], key=team["key"])
            cx_central.flush_dashboards(region=team["region"], key=team["key"])
