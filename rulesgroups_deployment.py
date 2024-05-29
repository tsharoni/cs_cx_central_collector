
import json
from os import environ

'''
The script,rulesgroups deployment, copies specific or all rule groups from one or more coralogix teams
to another team.

The script requires the teams.json file in the following format:
[
  {
    "account": "<account name>",
    "skip": false,
    "teams": [
      {
        "name": "<source team name>", <- multiple source can be defined
        "region": "<source team region>",
        "key": "<source team alerts key>",
        "source": true,
        "parsing_rule_groups": [1,2,5] <- an array of rules group to be copied. If missing , means all
      },
      {
        "name": "<target team name>",
        "region": "<target team region>",
        "key": "<target team alert key>",
        "target": true
      }
    ]
  }
]

The script uses:
    - cx_infra.get_rules to get all rules
    - cx_infra.parse_rules to parse the selected rule groups 
'''

import cx_infra

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

        # Initialization
        rules = {
            "companyRulesData": []
        }
        order = 1
        target_key = None
        target_region = None
        for team in account["teams"]:
            # Check if the team is a source for parsing rule
            if "source" in team and team["source"]:
                print("source team: {}".format(team["name"]))
                # Read all parsing rule groups from source
                source_rules = cx_infra.get_rules(region=team["region"], key=team["key"])
                # Check for 'parsing_rule_group'. If exists set the index of parsing rules as specified otherwise all
                if "parsing_rule_groups" in team:
                    rules_group_index = team['parsing_rule_groups']
                else:
                    rules_group_index = range(0, len(source_rules["companyRulesData"]))

                # Check sources and push the required rule groups to rules
                for index in rules_group_index:
                    source_rules['companyRulesData'][index]['order'] = order
                    rules['companyRulesData'].append(source_rules['companyRulesData'][index])
                    order += 1

            # if target set keys to target, in cases of multiple target, just the last one is selected
            if "target" in team and team["target"]:
                print("target team: {}".format(team["name"]))
                target_key = team['key']
                target_region = team['region']

        # if target is set post rules groups to target
        if target_key and target_region:
            payload = json.dumps(rules)
            cx_infra.post_rules(target_region, target_key, payload)
