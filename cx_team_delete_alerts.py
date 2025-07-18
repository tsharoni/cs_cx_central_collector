
import json
from os import environ

import cx_infra

#
# The scripts get the account name as variable and loop over the teams in file
# for each team it reads the users and delete them one by one
#

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
            # special setup to get the list of users
            try:
                alerts = cx_infra.get_alerts(region=team["region"], key=team["key"])
                for alert in alerts["alerts"]:
                    print('id = [{}] , name = [{}]'.format(alert['id'], alert['name']))
                    cx_infra.delete_alert(region=team["region"], key=team["key"] , alert_id=alert['id'])
                
                print("total {}".format(len(alerts["alerts"])))

            except Exception as e:
                print("Error:{}{}".format(e, 'cant read users'))
