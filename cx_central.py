
from os import environ

import cx_infra
import cx_otel

try:
    # set one time the otel provider, by variables
    provider = cx_otel.CoralogixOtel(
        environ.get('CX_ENDPOINT'),
        environ.get("CX_TOKEN"))
except:
    # or by the otel collector agent (no need to set the key)
    provider = cx_otel.CoralogixOtel(
        'http://localhost:4317/',
        'token is handled by agent')

cx_configuration = cx_otel.CoralogixOtelGauge("cx_configuration")

simulate = False


def set_attributes(account, team_id):
    cx_configuration.set_meta_attributes({'account': account, 'team_id': team_id})


def flush_alerts(region, key):

    labels = {'type': 'alert'}

    total = 0
    active = 0
    alerts_type = {}

    source_alerts_json = cx_infra.get_alerts(region, key)

    for alert in source_alerts_json['alerts']:
        total += 1
        alert_type = alert['log_filter']['filter_type']
        if alert_type == 'text':
            alert_type = 'standard'

        if alert_type not in alerts_type:
            alerts_type[alert_type] = {'total': 0, 'active': 0}

        alerts_type[alert_type]['total'] += 1

        if alert['is_active']:
            active += 1
            alerts_type[alert_type]['active'] += 1

    for alert_type in alerts_type:
        labels["alert_type"] = alert_type
        labels["active"] = False
        cx_configuration.flush_results(provider, labels, alerts_type[alert_type]['total']-alerts_type[alert_type]['active'])
        labels["active"] = True
        cx_configuration.flush_results(provider, labels, alerts_type[alert_type]['active'])
        labels.pop("active")

    print('total alerts = {}; active={} {}'.format(total, active, alerts_type))


def flush_webhooks(region, key):

    labels = {'type': 'webhook'}
    total_webhook = 0
    webhooks = cx_infra.get_webhooks(region, key)

    webhook_types = {}
    for webhook in webhooks:
        total_webhook += 1
        webhook_type = webhook['integration_type']['label']
        if webhook_type in webhook_types:
            webhook_types[webhook_type] += 1
        else:
            webhook_types[webhook_type] = 1

    for webhook_type in webhook_types:
        labels["webhook_type"] = webhook_type
        cx_configuration.flush_results(provider, labels, webhook_types[webhook_type])

    print('total webhooks = {} {}'.format(total_webhook, webhook_types))


def flush_e2m(region, key):

    labels = {'type': 'e2m'}
    json_data = cx_infra.get_e2m(region, key)

    if not json_data:
        return

    e2m_types = {}

    for e2m in json_data['e2m']:
        if e2m['type'] in e2m_types:
            e2m_types[e2m['type']] += 1
        else:
            e2m_types[e2m['type']] = 1

    for e2m_type in e2m_types:
        labels['e2m_type'] = e2m_type
        cx_configuration.flush_results(provider, labels, e2m_types[e2m_type])

    print("total e2m = {} {}".format(len(json_data['e2m']), e2m_types))


def flush_recording_rule(region, key):

    labels = {'type': 'recording_rule'}
    json_data = cx_infra.get_recording_rules(region, key)

    if json_data:
        cx_configuration.flush_results(provider, labels, len(json_data['ruleGroups']))
        print("total recording rule = {}".format(len(json_data['ruleGroups'])))


def flush_apm_services(region, key):

    labels = {'type': 'apm'}
    json_data = cx_infra.get_apm_services(region, key)

    if not json_data:
        return

    services = {}
    services_type = {}
    for service in json_data['services']:
        service_name = service['name']
        if service['technology'] in services:
            services[service['technology']] += 1
        else:
            services[service['technology']] = 1
        if service['type'] in services_type:
            services_type[service['type']] += 1
        else:
            services_type[service['type']] = 1

    for service in services:
        labels["technology"] = service
        cx_configuration.flush_results(provider, labels, services[service])
    for service_type in services_type:
        labels["service_type"] = service_type
        cx_configuration.flush_results(provider, labels, services_type[service_type])

    print("total APM services = {}, Type: {}, Technology: {}".format(
        len(json_data['services']), services_type, services))


def flush_slo(region, key):

    labels = {'type': 'slo'}
    json_data = cx_infra.get_slo(region, key)

    if not json_data:
        return

    slos = {'errorSli': 0, 'latencySli': 0}

    for slo in json_data['slos']:
        if 'errorSli' in slo:
            slos['errorSli'] += 1
        elif 'latencySli' in slo:
            slos['latencySli'] += 1

    for slo in slos:
        labels['slo_type'] = slo
        cx_configuration.flush_results(provider, labels, slos[slo])

    print("total slo = {} {}".format(len(json_data['slos']), slos))


def flush_dashboards(region, key):

    dashboards = cx_infra.get_dashboards(region, key)
    if not dashboards:
        print('Failed to retrieve dashboards')
        return

    total_cx_dashboards = len(dashboards)

    panels_type = {}
    for dashboard_id in dashboards:
        dashboard_data = cx_infra.get_dashboard_widgets(region, key, dashboard_id)

        if not dashboard_data:
            continue

        for section in dashboard_data['dashboard']['layout']['sections']:
            if 'rows' not in section:
                continue
            for row in section['rows']:
                for widget in row['widgets']:
                    widget_type = list(widget['definition'].keys())[0]
                    if widget_type in panels_type:
                        panels_type[widget_type] += 1
                    else:
                        panels_type[widget_type] = 1

    labels = {'type': 'cx_dashboard'}
    cx_configuration.flush_results(provider, labels, total_cx_dashboards)
    labels['type'] = 'cx_widget'
    for panel_type in panels_type:
        labels['widget_type'] = panel_type
        cx_configuration.flush_results(provider, labels, panels_type[panel_type])

    print("total cx dashboard = {}".format(total_cx_dashboards))


def flush_tco(region, key):

    labels = {'type': 'tco_policy'}
    json_data = cx_infra.get_tco(region, key)

    if not json_data:
        return

    tco_policies = {'SPANS': {}, 'LOGS': {}}
    for tco_policy in json_data['policies']:
        if 'logRules' in tco_policy:
            tco_policy_type = 'LOGS'
        else:
            tco_policy_type = 'SPANS'

        priority = tco_policy['priority']
        if priority not in tco_policies[tco_policy_type]:
            tco_policies[tco_policy_type][priority] = {}
            tco_policies[tco_policy_type][priority]['total'] = 0
            tco_policies[tco_policy_type][priority]['enabled'] = 0

        tco_policies[tco_policy_type][priority]['total'] += 1
        if tco_policy['enabled']:
            tco_policies[tco_policy_type][priority]['enabled'] += 1

    for policy_type in tco_policies:
        labels['policy_type'] = policy_type
        for priority in tco_policies[policy_type]:
            labels['priority'] = priority
            labels['enabled'] = False
            cx_configuration.flush_results(
                provider,
                labels,
                tco_policies[policy_type][priority]['total'] -
                tco_policies[policy_type][priority]['enabled'])
            labels['enabled'] = True
            cx_configuration.flush_results(
                provider,
                labels,
                tco_policies[policy_type][priority]['enabled'])
            labels.pop('enabled')

    print(tco_policies)


def flush_tco_overrides(region, key):

    labels = {'type': 'tco_overrides'}

    overrides = cx_infra.get_tco_overides(region, key)

    if overrides:
        cx_configuration.flush_results(provider, labels, len(overrides))
        print('total tco overrides = {}'.format(len(overrides)))


def flush_rules(region, key):

    labels = {'type': 'rules_group'}

    rules = cx_infra.get_rules(region, key)

    total_rules_group = 0
    total_rules = 0
    rules_type = {}
    for rules_group in rules['companyRulesData']:
        total_rules_group += 1
        for rule_group in rules_group['rulesGroups']:
            for rule in rule_group['rules']:
                total_rules += 1
                if rule['type'] in rules_type:
                    rules_type[rule['type']] += 1
                else:
                    rules_type[rule['type']] = 1

    cx_configuration.flush_results(provider, labels, total_rules_group)

    labels["type"] = "parsing_rule"

    for rule_type in rules_type:
        labels["parsing_rule_type"] = rule_type
        cx_configuration.flush_results(provider, labels, rules_type[rule_type])

    print('total rules groups = {}; total rules = {} {}'.format(
        total_rules_group,
        total_rules,
        rules_type)
    )


def flush_users(region, key):

    labels = {'type': 'user'}

    users = cx_infra.get_users(region, key)

    total_inactive = 0
    total_active = 0
    for user in users["data"]:
        labels["active"] = user["isActive"]
        labels["username"] = user["username"]
        labels["created_at"] = user["created_at"]
        cx_configuration.flush_results(provider, labels, 1)
        if user["isActive"]:
            total_active += 1
        else:
            total_inactive += 1
    labels = {'type': 'user','active': True}
    cx_configuration.flush_results(provider, labels, total_active)
    labels = {'type': 'user','active': False}
    cx_configuration.flush_results(provider, labels, total_inactive)

    print('total users = {}; inactive = {}'.format(
        total_active + total_inactive,
        total_inactive)
    )


def flush_grafana(region, key):

    labels = {'type': 'grafana_folder'}

    total_grafana_dashboards = 0
    total_grafana_panels = 0
    total_grafana_folders = 0
    panels_type = {}
    dashboards = cx_infra.get_grafana_dashboards(region, key)

    for dashboard in dashboards:
        dashboards_panels = cx_infra.get_grafana_dashboard_widgets(region, key, dashboard['uid'])
        if not dashboards_panels:
            continue
        try:
            for dashboard_panels in dashboards_panels['dashboard']['panels']:
                if dashboard_panels['type'] in panels_type:
                    panels_type[dashboard_panels['type']] += 1
                else:
                    panels_type[dashboard_panels['type']] = 1

                total_grafana_panels += 1
            total_grafana_dashboards += 1
        except Exception as e:
            total_grafana_folders += 1

    cx_configuration.flush_results(provider, labels, total_grafana_folders)

    labels["type"] = "grafana_dashboard"
    cx_configuration.flush_results(provider, labels, total_grafana_dashboards)

    labels["type"] = "grafana_panel"

    for panel_type in panels_type:
        labels["panel_type"] = panel_type
        cx_configuration.flush_results(provider, labels, panels_type[panel_type])

    print("total grafana folders = {}; dashboards = {}; panels = {} {}".format(
        total_grafana_folders,
        total_grafana_dashboards,
        total_grafana_panels,
        panels_type)
    )

