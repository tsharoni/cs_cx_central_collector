
import json
from os import environ

import cx_infra
import cx_central

#
# The scripts get the account name as variable and loop over the teams in file
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
                users = cx_infra.get_users_scim(region=team["region"], key=team["key"])

                for user in users["Resources"]:
                    print('id = {} , username = {}'.format(user["id"],user["userName"]))
                
                print("total {}".format(len(users["Resources"])))

            except Exception as e:
                print("Error:{}{}".format(e, 'cant read users'))
