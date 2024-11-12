import json,argparse
from mako.template import Template
from os import environ

from cx_infra import create_dashboard, delete_dashboard, replace_dashboard, get_dashboards


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
    dashboards = get_dashboards(region, key)
    for dashboard in dashboards:
        if dashboards[dashboard] == dashboard_name:
            return dashboard

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('dashboard_name', help="add dashboard name mako file")
    parser.add_argument('--params', nargs="+", help="parameters to render the file in key=value format")

    args = parser.parse_args()

    params_dict = parse_unknown_args(args.params) if args.params else {}
    params_dict['__range'] = '${__range}'

    file_path = "cx_usage_dashboard.mako"
    with open(file_path, 'r') as file:
        file_content = file.read()

    f = open('teams.json')
    teams_json = json.load(f)

    account_env = environ.get('account')

    for account in teams_json:
        if account_env != account['account'] and account_env != 'all':
            continue

        if 'skip' in account and account['skip']:
            continue

        print("\naccount: {}".format(account['account']))

        for team in account['teams']:
            print("team: {}".format(team['name']))

            params_dict['team_name'] = team['name']
            rendered_file = Template(file_content).render(**params_dict)
            dashboard_json = json.loads(rendered_file)

            del dashboard_json['updatedAt']
            dashboard_id = retrieve_dashboard_id(dashboard_json['dashboard']['name'], team['region'], team['key'])

            if dashboard_id:
                dashboard_json['dashboard']['id'] = dashboard_id
                replace_dashboard(
                    region=team['region'],
                    key=team['key'],
                    dashboard_data=json.dumps(dashboard_json)
                )
            else:
                del dashboard_json['dashboard']['id']
                create_dashboard(
                    region=team['region'],
                    key=team['key'],
                    dashboard_data=json.dumps(dashboard_json)
                )


