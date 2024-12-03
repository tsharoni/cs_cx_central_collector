import json, argparse
from mako.template import Template

from cx_infra import create_dashboard, replace_dashboard, get_dashboards


##########################################################################################
# custom_dashboard_deployment receives:
#    dashboard file as a mako file template
#    key-value pairs to replace placeholders(keys) in template with values
#
# to launch the script use:
#    python3 custom_dashboard_deployment dashboard.mako --params key1=value1 key2=value2
#
# the template should contain the keys/placeholder in ${<key>} format like:
#    ..."name": "[Coralogix] ${team_name} Data Usage and Cost estimate"...
#
# In the mako file , the ${team_name}, if added to template, would be replaced with the
#    team_name from the teams.json
##########################################################################################


def parse_unknown_args(args):
    """Parse unknown arguments in key=value format into a dictionary."""
    parsed_args = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)  # Split on the first '=' only
            parsed_args[key] = value
        else:
            raise ValueError(f"Argument '{arg}' is not in key=value format.")
    return parsed_args


def retrieve_dashboard_id(dashboard_name, region, key):
    # retrieves the ID from the name of the dashboard
    dashboards = get_dashboards(region, key)
    for dashboard in dashboards:
        if dashboards[dashboard] == dashboard_name:
            return dashboard


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dashboard_file', help="add dashboard name mako file")
    parser.add_argument('--account', help="add the account name for dashboards deployment")
    parser.add_argument('--params', nargs="+", help="parameters to render the file in key=value format")

    args = parser.parse_args()

    params_dict = parse_unknown_args(args.params) if args.params else {}
    params_dict['__range'] = '${__range}'

    file_path = args.dashboard_file
    with open(file_path, 'r') as file:
        file_content = file.read()

    f = open('teams.json')
    teams_json = json.load(f)

    account_env = args.account

    for account in teams_json:
        if account_env != account['account'] and account_env != 'all':
            continue

        if 'skip' in account and account['skip']:
            continue

        print("\naccount: {}".format(account['account']))

        for team in account['teams']:
            print("team: {}".format(team['name']))

            # rendering the mako file from the parameters provided
            params_dict['team_name'] = team['name']
            rendered_file = Template(file_content).render(**params_dict)
            dashboard_json = json.loads(rendered_file)

            # removing updatedAt as it is not accepted by the service
            del dashboard_json['updatedAt']
            # check if the dashboard already exists by retrieving the dashboard_id
            dashboard_id = retrieve_dashboard_id(dashboard_json['dashboard']['name'], team['region'], team['key'])

            if dashboard_id:
                # replace if exists
                dashboard_json['dashboard']['id'] = dashboard_id
                replace_dashboard(
                    region=team['region'],
                    key=team['key'],
                    dashboard_data=json.dumps(dashboard_json)
                )
            else:
                # create if the ID doesn't exist(remove the ID to create a new one)
                del dashboard_json['dashboard']['id']
                create_dashboard(
                    region=team['region'],
                    key=team['key'],
                    dashboard_data=json.dumps(dashboard_json)
                )


