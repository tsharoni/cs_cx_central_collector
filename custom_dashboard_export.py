import json, argparse
from os import environ

from cx_infra import get_dashboards, get_dashboard_file


##########################################################################################
# custom_dashboard_export receives:
#    dashboard_name - the name of the dashboard to be exported
#    team_name - to search the requested dashboard at (as defiend in the teams.json file)
#
# to launch the script use:
#    python3 custom_dashboard_export --dashboard_name "<dashboard name>" --team_name <team_name>
#
#
# The script will export the dashboard data to a json file name <team_name>-<dashboard_id>.json
#
##########################################################################################


def retrieve_dashboard_id(dashboard_name, region, key):
    # retrieves the ID from the name of the dashboard
    dashboards = get_dashboards(region, key)
    for dashboard in dashboards:
        if dashboards[dashboard] == dashboard_name:
            return dashboard


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dashboard_name', help="add dashboard name to export")
    parser.add_argument('--team_name', help="add the team name to export from")

    args = parser.parse_args()

    f = open('teams.json')
    teams_json = json.load(f)

    account_env = environ.get('account')

    for account in teams_json:
        if account_env != account['account'] and account_env != 'all':
            continue

        if 'skip' in account and account['skip']:
            continue

        for team in account['teams']:
            if team['name'] != args.team_name:
                continue

            # check if the dashboard already exists by retrieving the dashboard_id
            dashboard_id = retrieve_dashboard_id(args.dashboard_name, team['region'], team['key'])

            if dashboard_id:
                dashboard_file = get_dashboard_file(team['region'], team['key'], dashboard_id)

                if not dashboard_file:
                    print('dashboard file cannot be exported for [{}]'.format(dashboard_id))

                filename = "{}-{}.json".format(team['name'], dashboard_id)
                output = open(filename, 'w')
                output.write(dashboard_file)
                output.close()
                break
            else:
                print('dashboard [{}] cannot be found'.format(args.dashboard_name))



