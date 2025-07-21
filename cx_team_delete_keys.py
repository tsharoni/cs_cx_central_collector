
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
            try:
                keys = cx_infra.get_api_team_keys(region=team["region"], key=team["key"])
                if len(keys) == 0:
                    continue

                print('deleting team keys')
                for key in keys["keys"]:
                    print('key_id [{}], key_name [{}]'.format(key["apiKey"]["id"],key["apiKey"]["keyName"]))
                    cx_infra.delete_api_key(region=team["region"], key=team["key"] , api_key_id=key["apiKey"]["id"])
                
                print("total {}".format(len(keys["keys"])))

            except Exception as e:
                print("Error:{}{}".format(e, 'cant read keys'))

            try:
                keys = cx_infra.get_api_send_keys(region=team["region"], key=team["key"])
                if len(keys) == 0:
                    continue

                print('deleting send data keys')
                for key in keys["keys"]:
                    print('key_id [{}], key_name [{}]'.format(key["apiKey"]["id"],key["apiKey"]["keyName"]))
                    cx_infra.delete_api_key(region=team["region"], key=team["key"] , api_key_id=key["apiKey"]["id"])
                
                print("total {}".format(len(keys["keys"])))
            
            except Exception as e:
                print("Error:{}{}".format(e, 'cant read keys'))

