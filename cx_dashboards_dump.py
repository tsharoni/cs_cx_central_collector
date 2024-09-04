import cx_infra
import json
from os import environ


def dump_dashboards(region, key, file_prefix):

    dashboards = cx_infra.get_dashboards(region, key)
    if not dashboards:
        print('Failed to retrieve dashboards')
        return

    for dashboard_id in dashboards:
        dashboard_file = cx_infra.get_dashboard_file(region, key, dashboard_id)

        if not dashboard_file:
            continue

        output = open("{}-{}.json".format(file_prefix, dashboard_id), 'w')
        output.write(dashboard_file)
        output.close()


def dump_grafana_dashboards(region, key, file_prefix):

    dashboards = cx_infra.get_grafana_dashboards(region, key)
    if not dashboards:
        print('Failed to retrieve grafana dashboards')
        return

    for dashboard in dashboards:
        dashboard_file = cx_infra.get_grafana_dashboard_file(region, key, dashboard['uid'])

        if not dashboard_file:
            continue

        output = open("{}-{}.json".format(file_prefix, dashboard['uid']), 'w')
        output.write(dashboard_file)
        output.close()


def dump_alerts(region, key, file_prefix):

    alerts = cx_infra.call_http_extended(cx_infra.coralogix_alerts_url.format(cx_infra.region_domains[region]), key)
    if not alerts:
        print('Failed to retrieve alerts')
        return

    output = open("{}.json".format(file_prefix), 'w')
    output.write(alerts)
    output.close()


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
            dump_dashboards(region=team["region"], key=team["key"], file_prefix="{}-cx_dashboards".format(team["name"]))
            dump_grafana_dashboards(region=team["region"], key=team["key"], file_prefix="{}-grafana_dashboards".format(team["name"]))
            dump_alerts(region=team["region"], key=team["key"], file_prefix="{}-alerts".format(team["name"]))

