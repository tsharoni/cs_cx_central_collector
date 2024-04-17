
import requests
import json
from os import environ
from opentelemetry import metrics
from opentelemetry.metrics import Observation, CallbackOptions
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

import subprocess

region_domains = {
    'usprod1': "coralogix.us",
    'usprod1-vpc': "coralogix.us",
    'prod': "coralogix.com",
    'cx498': "cx498.coralogix.com",
    'india': "coralogix.in",
    'eu2': "eu2.coralogix.com",
    'sg': "coralogixsg.com"
}

coralogix_alerts_url = "https://api.{}/api/v1/external/alerts"
coralogix_parsing_url = "https://api.{}/api/v1/external/rules"
coralogix_webhook_url = "https://api.{}/api/v1/external/integrations/{}"
coralogix_grafana_url = "https://ng-api-http.{}/grafana/api/search"
coralogix_grafana_panels_url = "https://ng-api-http.{}/grafana/api/dashboards/uid/{}"
coralogix_tco_overrides_url = "https://api.{}/api/v1/external/tco/overrides"
coralogix_custom_enrichment_url = "https://webapi.{}/api/v1/external/custom-enrichments"
coralogix_grpc_url = "ng-api-grpc.{}:443"

GRPC_E2M_METHOD = "com.coralogixapis.events2metrics.v2.Events2MetricService.ListE2M"
GRPC_RECORDING_RULE_METHOD = "rule_manager.groups.RuleGroups.List"
GRPC_APM_SERVICES_METHOD = "com.coralogixapis.apm.services.v1.ApmServiceService/ListApmServices"
GRPC_SLO_METHOD = "com.coralogixapis.apm.services.v1.ServiceSloService/ListServiceSlos"
GRPC_TCO_POLICIES = "com.coralogix.quota.v1.PoliciesService.GetCompanyPolicies"
GRPC_DASHBOARD_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardCatalogService/GetDashboardCatalog"
GRPC_DASHBOARD_GET_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardsService/GetDashboard"

def get_gauge_callback(_: CallbackOptions):

    yield Observation(value, attributes)


# define the OTEL metrics exporter. Need to define the CX_ENDPOINT and CX_TOKEN environment variables
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(
        endpoint=environ.get('CX_ENDPOINT'),
        headers=[('authorization', "Bearer " + environ.get("CX_TOKEN"))])
)

resource = Resource(attributes={
    SERVICE_NAME: "counter-metrics"
})

provider = MeterProvider(resource=resource, metric_readers=[reader])

metrics.set_meter_provider(provider)

gauge = metrics.get_meter(__name__).create_observable_gauge(
    callbacks=[get_gauge_callback],
    name="cx_configuration",
    description="cx_configuration",
    unit=""
    )

value = 0
attributes = {}


def call_http(url, key):
    try:
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(key)}
        response = requests.request("GET", url, headers=headers, data={})
        return response.text
    except:
        print('http error')


def call_grpc(region, key, method, params=None):

    server_address = coralogix_grpc_url.format(region_domains[region])

    # Replace with your actual Bearer token
    bearer_token = key

    # Replace with your gRPC service and method
    grpc_service_method = method

    # Build the grpcurl command
    grpcurl_command = [
        'grpcurl',
        '-H', f'Authorization: Bearer {bearer_token}']
    if params:
        grpcurl_command.append('-d')
        grpcurl_command.append(f'{params}')

    grpcurl_command.append(server_address)
    grpcurl_command.append(grpc_service_method)

    error = ""
    try:
        # Launch the subprocess
        process = subprocess.Popen(grpcurl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Wait for the subprocess to finish and get the output and error
        output, error = process.communicate()

        # Print the output and error
        json_data = json.loads(output)

        return json_data
        # print("Return Code:", return_code)

    except Exception as e:
        print("Error:{}{}".format(e, error))


def flush_results(labels, result):

    global value
    global attributes

    attributes = attributes | labels

    value = result
    print('flushing labels:{} value: {}'.format(attributes, value))
    provider.force_flush()

    for label in labels:
        attributes.pop(label)


def display_alerts(region, key):

    labels = {'type': 'alert'}

    total = 0
    active = 0
    alerts_type = {}

    source_alerts_json = json.loads(call_http(coralogix_alerts_url.format(region_domains[region]), key))

    for alert in source_alerts_json['alerts']:
        #print ("alert name:[{}] , alert query: [{}".format(alert["name"], alert["log_filter"]))
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
        flush_results(labels, alerts_type[alert_type]['total']-alerts_type[alert_type]['active'])
        labels["active"] = True
        flush_results(labels, alerts_type[alert_type]['active'])
        labels.pop("active")

    print('total alerts = {}; active={} {}'.format(total, active, alerts_type))


def display_webhooks(region, key):

    labels = {'type': 'webhook'}
    total_webhook = 0
    webhooks = json.loads(call_http(coralogix_webhook_url.format(region_domains[region], ""), key))

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
        flush_results(labels, webhook_types[webhook_type])

    print('total webhooks = {} {}'.format(total_webhook, webhook_types))


def display_e2m(region, key):

    labels = {'type': 'e2m'}
    json_data = call_grpc(region, key, GRPC_E2M_METHOD)

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
        flush_results(labels, e2m_types[e2m_type])

    print("total e2m = {} {}".format(len(json_data['e2m']), e2m_types))


def display_recording_rule(region, key):

    labels = {'type': 'recording_rule'}
    json_data = call_grpc(region, key, GRPC_RECORDING_RULE_METHOD)

    if json_data:
        flush_results(labels, len(json_data['ruleGroups']))
        print("total recording rule = {}".format(len(json_data['ruleGroups'])))


def display_apm_services(region, key):

    labels = {'type': 'apm'}
    json_data = call_grpc(region, key, GRPC_APM_SERVICES_METHOD)

    if not json_data:
        return

    services = {}
    services_type = {}
    for service in json_data['services']:
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
        flush_results(labels, services[service])
    for service_type in services_type:
        labels["service_type"] = service_type
        flush_results(labels, services_type[service_type])

    print("total APM services = {}, Type: {}, Technology: {}".format(
        len(json_data['services']), services_type, services))


def display_slo(region, key):

    labels = {'type': 'slo'}
    json_data = call_grpc(region, key, GRPC_SLO_METHOD)

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
        flush_results(labels, slos[slo])

    print("total slo = {} {}".format(len(json_data['slos']), slos))


def display_dashboards(region, key):

    json_data = call_grpc(region, key, GRPC_DASHBOARD_METHOD)

    if not json_data:
        return

    total_cx_dashboards = len(json_data['items'])

    panels_type = {}
    for dashboard in json_data['items']:
        parameters = """{"dashboardId":"%s"}""" % (dashboard['id'])
        json_data = call_grpc(region, key, GRPC_DASHBOARD_GET_METHOD, parameters)
        for section in json_data['dashboard']['layout']['sections']:
            if 'rows' not in section:
                continue
            for row in section['rows']:
                for widget in row['widgets']:
                    widget_type = list(widget['definition'].keys())[0]
                    #if widget_type == 'lineChart':
                    #    print ('Coralogix dashboard: widget name [{}]'.format(widget['title']))
                    #    for query in widget['definition']['lineChart']['queryDefinitions']:
                    #        print('query [{}]'.format(query['query']))
                    #else:
                    #    print ('Coralogix dashboard: widget name [{}], query [{}]'.format(
                    #        widget['title'],
                    #        widget['definition'][widget_type]['query']))
                    if widget_type in panels_type:
                        panels_type[widget_type] += 1
                    else:
                        panels_type[widget_type] = 1

    labels = {'type': 'cx_dashboard'}
    flush_results(labels, total_cx_dashboards)
    labels['type'] = 'cx_widget'
    for panel_type in panels_type:
        labels['widget_type'] = panel_type
        flush_results(labels, panels_type[panel_type])

    print("total cx dashboard = {}".format(total_cx_dashboards))


def display_tco(region, key):

    labels = {'type': 'tco_policy'}
    json_data = call_grpc(region, key, GRPC_TCO_POLICIES)

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
            flush_results(labels,
                          tco_policies[policy_type][priority]['total'] -
                          tco_policies[policy_type][priority]['enabled'])
            labels['enabled'] = True
            flush_results(labels, tco_policies[policy_type][priority]['enabled'])
            labels.pop('enabled')

    print(tco_policies)


def display_tco_overrides(region, key):

    labels = {'type': 'tco_overrides'}

    overrides = json.loads(call_http(coralogix_tco_overrides_url.format(region_domains[region]), key))

    flush_results(labels, len(overrides))

    print('total tco overrides = {}'.format(len(overrides)))


def display_rules(region, key):

    labels = {'type': 'rules_group'}

    rules = json.loads(call_http(coralogix_parsing_url.format(region_domains[region]), key))

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

    flush_results(labels, total_rules_group)

    labels["type"] = "parsing_rule"

    for rule_type in rules_type:
        labels["parsing_rule_type"] = rule_type
        flush_results(labels, rules_type[rule_type])

    print('total rules groups = {}; total rules = {} {}'.format(
        total_rules_group,
        total_rules,
        rules_type)
    )


def display_grafana(region, key):

    labels = {'type': 'grafana_folder'}

    total_grafana_dashboards = 0
    total_grafana_panels = 0
    total_grafana_folders = 0
    panels_type = {}
    dashboards = json.loads(call_http(coralogix_grafana_url.format(region_domains[region]), key))

    for dashboard in dashboards:
        dashboards_panels = json.loads(call_http(
            coralogix_grafana_panels_url.format(region_domains[region], dashboard['uid']),
            key)
        )
        try:
            for dashboard_panels in dashboards_panels['dashboard']['panels']:
#                print ('Grafana dashboard panel [{}]'.format(dashboard_panels['title']))
#                for target in dashboard_panels['targets']:
#                    print ('datasource:[{}], query:[{}]'.format(target['datasource'],target['expr']))
                if dashboard_panels['type'] in panels_type:
                    panels_type[dashboard_panels['type']] += 1
                else:
                    panels_type[dashboard_panels['type']] = 1

                total_grafana_panels += 1
            total_grafana_dashboards += 1
        except Exception as e:
            total_grafana_folders += 1

    flush_results(labels, total_grafana_folders)

    labels["type"] = "grafana_dashboard"
    flush_results(labels, total_grafana_dashboards)

    labels["type"] = "grafana_panel"

    for panel_type in panels_type:
        labels["panel_type"] = panel_type
        flush_results(labels, panels_type[panel_type])

    print("total grafana folders = {}; dashboards = {}; panels = {} {}".format(
        total_grafana_folders,
        total_grafana_dashboards,
        total_grafana_panels,
        panels_type)
    )


if __name__ == '__main__':

    f = open('teams.json')
    teams_json = json.load(f)

    account_env = environ.get('account')
    for account in teams_json:
        if account_env != account["account"] and account_env != 'all':
            continue

        if "skip" in account and account["skip"]:
            continue

        attributes["account"] = account["account"]
        print("\naccount: {}".format(account["account"]))

        for team in account["teams"]:
            attributes["team_id"] = team["name"]
            print("team: {}".format(team["name"]))
            display_alerts(region=team["region"], key=team["key"])
            display_webhooks(region=team["region"], key=team["key"])
            display_rules(region=team["region"], key=team["key"])
            display_tco_overrides(region=team["region"], key=team["key"])
            display_grafana(region=team["region"], key=team["key"])
            display_e2m(region=team["region"], key=team["key"])
            display_tco(region=team["region"], key=team["key"])
            display_recording_rule(region=team["region"], key=team["key"])
            display_apm_services(region=team["region"], key=team["key"])
            display_slo(region=team["region"], key=team["key"])
            display_dashboards(region=team["region"], key=team["key"])
