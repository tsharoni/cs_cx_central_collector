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
    parser.add_argument('--region', help="add the team region name of the team")
    parser.add_argument('--key', help="add the api key to export the dashboard")
    parser.add_argument('--dashboard', help="add dashboard name to export")
    args = parser.parse_args()


    # check if the dashboard exists by retrieving the dashboard_id
    dashboard_id = retrieve_dashboard_id(args.dashboard, args.region, args.key)

    if dashboard_id:
        dashboard_file = get_dashboard_file(args.region, args.key, dashboard_id)

        if not dashboard_file:
            print('dashboard file cannot be exported for [{}]'.format(dashboard_id))

        filename = "dashboard-template-{}.mako".format(dashboard_id)
        output = open(filename, 'w')
        output.write(dashboard_file)
        output.close()
        print('dashboard template mako file [{}] created'.format(filename))
    else:
        print('dashboard [{}] cannot be found'.format(args.dashboard))



