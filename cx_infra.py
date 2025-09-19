import requests
import json

import re

import subprocess

region_domains = {
    'usprod1': "us1.coralogix.com",
    'usprod1-vpc': "coralogix.us",
    'prod': "coralogix.com",
    'cx498': "cx498.coralogix.com",
    'india': "coralogix.in",
    'eu2': "eu2.coralogix.com",
    'sg': "coralogixsg.com"
}

coralogix_alerts_url = "https://api.{}/api/v1/external/alerts"
coralogix_parsing_url = "https://api.{}/api/v1/external/rules"
coralogix_parsing_export_url = "https://api.{}/api/v1/external/rules/export"
coralogix_webhook_url = "https://api.{}/api/v1/external/integrations/{}"
coralogix_grafana_url = "https://ng-api-http.{}/grafana/api/search"
coralogix_grafana_panels_url = "https://ng-api-http.{}/grafana/api/dashboards/uid/{}"
coralogix_tco_overrides_url = "https://api.{}/api/v1/external/tco/overrides"
coralogix_custom_enrichment_url = "https://webapi.{}/api/v1/external/custom-enrichments{}{}"
coralogix_grpc_url = "ng-api-grpc.{}:443"
coralogix_users_url = "https://api.{}/api/v1/user/team/teammates"
coralogix_users_scim_url = "https://api.{}/scim/Users"
coralogix_users_scim_delete_url = "https://api.{}/scim/Users/{}"

GRPC_E2M_METHOD = "com.coralogixapis.events2metrics.v2.Events2MetricService.ListE2M"
GRPC_RECORDING_RULE_METHOD = "rule_manager.groups.RuleGroups.List"
GRPC_APM_SERVICES_METHOD = "com.coralogixapis.apm.services.v1.ApmServiceService/ListApmServices"
GRPC_SLO_METHOD = "com.coralogixapis.apm.services.v1.ServiceSloService/ListServiceSlos"
GRPC_TCO_POLICIES = "com.coralogix.quota.v1.PoliciesService.GetCompanyPolicies"
GRPC_DASHBOARD_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardCatalogService/GetDashboardCatalog"
GRPC_DASHBOARD_GET_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardsService/GetDashboard"
GRPC_VIEWS_METHOD = "com.coralogixapis.views.v1.services.ViewsService/ListViews"
GRPC_APM_DELETE = "com.coralogixapis.apm.services.v1.ApmServiceService/DeleteApmService"
GRPC_E2M_CREATE = "com.coralogixapis.events2metrics.v2.Events2MetricService.CreateE2M"
GRPC_DASHBOARD_CREATE = "com.coralogixapis.dashboards.v1.services.DashboardsService.CreateDashboard"
GRPC_DASHBOARD_DELETE = "com.coralogixapis.dashboards.v1.services.DashboardsService.DeleteDashboard"
GRPC_DASHBOARD_REPLACE = "com.coralogixapis.dashboards.v1.services.DashboardsService.ReplaceDashboard"
GRPC_API_TEAM_KEYS_GET = "com.coralogix.apikeys.v2.ApiKeysMgmtService/GetTeamApiKeys"
GRPC_API_SEND_KEYS_GET = "com.coralogix.apikeys.v2.ApiKeysMgmtService/GetSendDataApiKeys"
GRPC_API_KEY_DELETE = "com.coralogix.apikeys.v2.ApiKeysMgmtService/DeleteKey"

def replace_value_based_on_sibling(dictionary, target_key, sibling_key, sibling_value, new_value):
    for key, value in dictionary.items():
        # If the value is another dictionary, recurse into it
        if isinstance(value, dict):
            # Check if both sibling_key and target_key exist in the same dictionary level
            if sibling_key in value and target_key in value:
                # If sibling_key has the specific value, change the target_key's value
                if value[sibling_key] == sibling_value:
                    value[target_key] = new_value

            # Recurse deeper into nested dictionaries
            replace_value_based_on_sibling(value, target_key, sibling_key, sibling_value, new_value)

        # If the value is a list, check each element
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    replace_value_based_on_sibling(item, target_key, sibling_key, sibling_value, new_value)


def call_http_extended(url, key, method="GET", data={}, files={}, content_type='application/json'):
    headers = {
        'Authorization': 'Bearer {}'.format(key)
    }

    if content_type:
        headers['Content-Type'] = content_type

    try:
        response = requests.request(method, url, headers=headers, data=data, files=files)
        if response.text:
            return response.text
        else:
            return response.status_code
    except:
        print('http error')
        return


def call_grpc(region, key, method, params=None, data_output=True):
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
        if error != '':
            print("method: '{}' \n - {}".format(method, error))
            return {'status': 'ERROR'}

        elif data_output:
            json_data = json.loads(output)
            return json_data
        else:
            return output

    except Exception as e:
        print("Error:{}{}".format(e, error))


def delete_apm_services(region, key, pattern):
    pat = re.compile(r"{}".format(pattern))

    json_data = call_grpc(region, key, GRPC_APM_SERVICES_METHOD)

    if not json_data:
        return

    for service in json_data['services']:
        service_name = service['name']
        if re.fullmatch(pat, service_name):
            print("{} matches regex pattern /{}/ -  deleting!".format(service_name, pattern))
            parameters = """{"id":"%s"}""" % (service['id'])
            json_data = call_grpc(region, key, GRPC_APM_DELETE, parameters)
            continue
        else:
            print("{} does not match regex pattern /{}/".format(service_name, pattern))


def convert_dict_to_json(dict, value_label, target_label):
    json_output = ""
    comma = ""
    for item in dict:
        json_output = """%s%s{"%s":"%s","%s":"%s"}""" % (
            json_output,
            comma,
            value_label,
            item,
            target_label,
            dict[item]
        )
        comma = ","

    return json_output


def create_e2m(region,
               key,
               name,
               description,
               query="",
               severities="",
               metrics_list={},
               labels_list={},
               applications="",
               subsystems="",
               permutation=30000):
    labels_json = convert_dict_to_json(labels_list, "targetLabel", "sourceField")
    metrics_json = convert_dict_to_json(metrics_list, "targetBaseMetricName", "sourceField")

    parameters = """
    {"e2m": 
        {"name": "%s",
        "description": "%s",
        "metricFields": [%s],
        "metricLabels": [%s],
        "logs_query": 
            {"lucene": "%s",
            "severityFilters": [%s],
            "applicationnameFilters": [%s],
            "subsystemnameFilters": [%s]
            },
        "permutations_limit": %d,
        "type": "E2M_TYPE_LOGS2METRICS"}}
        """ % (name, description, metrics_json, labels_json, query, severities, applications, subsystems, permutation)

    parameters = parameters.replace(" ", "")

    json_data = call_grpc(region, key, GRPC_E2M_CREATE, parameters)
    print("{}".format(json_data))


def create_dashboard(region,
                     key,
                     dashboard_data):

    json_data = call_grpc(region,key,GRPC_DASHBOARD_CREATE, dashboard_data)
    if 'status' in json_data and json_data['status']=='ERROR':
        json_data = call_grpc(region, key, GRPC_DASHBOARD_REPLACE, dashboard_data)

    print("{}".format(json_data))


def replace_dashboard(region,
                      key,
                      dashboard_data):

    json_data = call_grpc(region, key, GRPC_DASHBOARD_REPLACE, dashboard_data)

    print("{}".format(json_data))


def delete_dashboard(region,
                     key,
                     dashboard_data):

    json_data = call_grpc(region,key,GRPC_DASHBOARD_DELETE, dashboard_data)
    print("{}".format(json_data))


def get_views(region, key):
    views = {}
    json_data = call_grpc(region, key, GRPC_VIEWS_METHOD)

    if not json_data:
        return {}

    for view in json_data['views']:
        views[view['id']] = view['name']

    print('number of views added [{}]'.format(len(views)))

    return views


def get_dashboards(region, key):
    dashboards = {}
    json_data = call_grpc(region, key, GRPC_DASHBOARD_METHOD)

    if not json_data:
        return {}

    for dashboard in json_data['items']:
        dashboards[dashboard['id']] = dashboard['name']

    print('number of dashboard retrieved [{}]'.format(len(dashboards)))

    return dashboards


def get_dashboard(region, key, dashboard_id):
    parameters = """{"dashboardId":"%s"}""" % dashboard_id
    dashboard_data = call_grpc(region, key, GRPC_DASHBOARD_GET_METHOD, parameters)
    return dashboard_data


def get_dashboard_file(region, key, dashboard_id):
    parameters = """{"dashboardId":"%s"}""" % dashboard_id
    dashboard_file = call_grpc(region, key, GRPC_DASHBOARD_GET_METHOD, parameters, data_output=False)
    return dashboard_file


def get_e2m(region, key):
    json_data = call_grpc(region, key, GRPC_E2M_METHOD)
    return json_data


def get_recording_rules(region, key):
    json_data = call_grpc(region, key, GRPC_RECORDING_RULE_METHOD)
    return json_data


def get_apm_services(region, key):
    json_data = call_grpc(region, key, GRPC_APM_SERVICES_METHOD)
    return json_data


def get_slo(region, key):
    json_data = call_grpc(region, key, GRPC_SLO_METHOD)
    return json_data


def get_tco(region, key):
    json_data = call_grpc(region, key, GRPC_TCO_POLICIES)
    return json_data


def get_api_send_keys(region, key):
    json_data = call_grpc(region, key, GRPC_API_SEND_KEYS_GET)
    return json_data


def get_api_team_keys(region, key):
    json_data = call_grpc(region, key, GRPC_API_TEAM_KEYS_GET)
    return json_data


def delete_api_key(region, key, api_key_id):
    parameters = """{"key_id":"%s"}""" % api_key_id
    json_data = call_grpc(region, key, GRPC_API_KEY_DELETE, parameters, data_output=False)
    return json_data



def get_tco_overides(region, key):
    response = call_http_extended(coralogix_tco_overrides_url.format(region_domains[region]), key)
    if response:
        return json.loads(response)


def get_alerts(region, key):
    return json.loads(call_http_extended(coralogix_alerts_url.format(region_domains[region]), key))


def delete_alert(region, key, alert_id):
    response = call_http_extended(url=coralogix_alerts_url.format(region_domains[region]),
                                  key=key,
                                  method="DELETE",
                                  data=json.dumps({"id": alert_id})
                                  )

    print('alert-id [{}] - status_code [{}]'.format(alert_id,response))


def create_alert(region, key, alert_obj):
    del alert_obj['id']
    del alert_obj['unique_identifier']
    del alert_obj['created_at']
    del alert_obj['lastTriggered']
    if alert_obj['condition']['promql_text']:
        if 'group_by_lvl2' in alert_obj['condition']:
            del alert_obj['condition']['group_by_lvl2']
        if 'metric_field' in alert_obj['condition']:
            del alert_obj['condition']['metric_field']
        if 'metric_source' in alert_obj['condition']:
            del alert_obj['condition']['metric_source']
        if 'arithmetic_operator' in alert_obj['condition']:
            del alert_obj['condition']['arithmetic_operator']
        if 'group_by' in alert_obj['condition']:
            del alert_obj['condition']['group_by']
        #if 'log_filter' in alert_obj:
        #    del alert_obj['log_filter']

    payload = json.dumps(alert_obj)

    response = call_http_extended(url=coralogix_alerts_url.format(region_domains[region]),
                                  key=key,
                                  method="POST",
                                  data=payload)

    print('Alert [{}] - {}'.format(alert_obj['name'],response))


def get_users_scim(region, key):
    return json.loads(call_http_extended(coralogix_users_scim_url.format(region_domains[region]), key))



def delete_user_scim(region, key, user_id):
    response = call_http_extended(url=coralogix_users_scim_delete_url.format(region_domains[region], user_id),
                                  key=key,
                                  method="DELETE",
                                  data={})

    print('user [{}] - status_code [{}]'.format(user_id,response))


def get_users(region, key):
    return json.loads(call_http_extended(coralogix_users_url.format(region_domains[region]), key))


def get_rules(region, key):
    return json.loads(call_http_extended(coralogix_parsing_url.format(region_domains[region]), key))


def post_rules(region, key, rules):
    output = call_http_extended(
        url=coralogix_parsing_export_url.format(region_domains[region]),
        key=key,
        method='POST',
        data=rules
    )
    return output


def get_grafana_dashboards(region, key):
    return json.loads(call_http_extended(coralogix_grafana_url.format(region_domains[region]), key))


def get_grafana_dashboard_widgets(region, key, dashboard_id):
    response = call_http_extended(
        coralogix_grafana_panels_url.format(region_domains[region], dashboard_id),
        key)
    if response != '':
        return json.loads(response)


def get_grafana_dashboard_file(region, key, dashboard_id):
    response = call_http_extended(
        coralogix_grafana_panels_url.format(region_domains[region], dashboard_id),
        key)
    if response != '':
        grafana_json = json.loads(response)
        # return none if object is not a dashboard
        if 'panels' not in grafana_json['dashboard']:
            return

        # add inputs
        grafana_json["dashboard"]["__inputs"] = [
            {
                "name": "DS_LOGS",
                "label": "Logs",
                "description": "",
                "type": "datasource",
                "pluginId": "elasticsearch",
                "pluginName": "Elasticsearch"
            },
            {
                "name": "DS_METRICS",
                "label": "Metrics",
                "description": "",
                "type": "datasource",
                "pluginId": "prometheus",
                "pluginName": "Prometheus"
            }
        ]

        replace_value_based_on_sibling(grafana_json, target_key='uid', sibling_key='type', sibling_value='prometheus',
                                       new_value='${DS_METRICS}')

        replace_value_based_on_sibling(grafana_json, target_key='uid', sibling_key='type', sibling_value='elasticsearch',
                                       new_value='${DS_LOGS}')

        json_dump = json.dumps(grafana_json['dashboard'])
        return json_dump


def get_webhooks(region, key):
    return json.loads(call_http_extended(coralogix_webhook_url.format(region_domains[region], ""), key))


def send_enrichment(region, key, dictionary, enrichment_file_name):
    filename = "{}.csv".format(enrichment_file_name)
    f = open(filename, 'w')

    f.write("key,value\r\n")

    for item in dictionary:
        # replacing comma with semicolon
        item_value = dictionary[item].replace(',', ';')
        f.write("{},{}\r\n".format(item, item_value))

    f.close()

    payload = {
        "name": "{}".format(enrichment_file_name),
        "description": "{}".format(enrichment_file_name)
    }

    files = {
        "file": (filename, open(filename, 'rb'))
    }

    enrichment_url = coralogix_custom_enrichment_url.format(region_domains[region], '', '')
    # check for existing custom enrichment
    response = json.loads(call_http_extended(
        enrichment_url,
        key
    ))

    enrichment_id = None
    for custom_enrichment in response:
        if custom_enrichment['name'] == enrichment_file_name:
            enrichment_id = custom_enrichment['id']
            break

    if enrichment_id:
        # Update existing
        method = 'PUT'
        enrichment_url = coralogix_custom_enrichment_url.format(region_domains[region], '/', enrichment_id)
    else:
        # Create a new one
        method = 'POST'

    response = json.loads(call_http_extended(
        url=enrichment_url,
        key=key,
        method=method,
        data=payload,
        files=files,
        content_type=None
    ))
    print(response)

    files['file'][1].close()
