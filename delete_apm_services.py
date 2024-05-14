
import cx_infra
import json
from os import environ

if __name__ == '__main__':

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
            print("team: {}".format(team["name"]))
            cx_infra.delete_apm_services(
                region=team["region"],
                key=team["key"],
                pattern="unknown_service:java")
