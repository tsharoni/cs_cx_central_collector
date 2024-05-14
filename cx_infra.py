
import requests
import json
from os import environ

import re

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
coralogix_custom_enrichment_url = "https://webapi.{}/api/v1/external/custom-enrichments{}{}"
coralogix_grpc_url = "ng-api-grpc.{}:443"

GRPC_E2M_METHOD = "com.coralogixapis.events2metrics.v2.Events2MetricService.ListE2M"
GRPC_RECORDING_RULE_METHOD = "rule_manager.groups.RuleGroups.List"
GRPC_APM_SERVICES_METHOD = "com.coralogixapis.apm.services.v1.ApmServiceService/ListApmServices"
GRPC_SLO_METHOD = "com.coralogixapis.apm.services.v1.ServiceSloService/ListServiceSlos"
GRPC_TCO_POLICIES = "com.coralogix.quota.v1.PoliciesService.GetCompanyPolicies"
GRPC_DASHBOARD_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardCatalogService/GetDashboardCatalog"
GRPC_DASHBOARD_GET_METHOD = "com.coralogixapis.dashboards.v1.services.DashboardsService/GetDashboard"

GRPC_APM_DELETE = "com.coralogixapis.apm.services.v1.ApmServiceService/DeleteApmService"
GRPC_E2M_CREATE = "com.coralogixapis.events2metrics.v2.Events2MetricService.CreateE2M"


def call_http_extended(url, key, method="GET", data={}, files={}):
    try:
        headers = {'Authorization': 'Bearer {}'.format(key)}
        response = requests.request(method, url, headers=headers, data=data,files=files)
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


def get_dashboards(region, key):

    dashboards = {}
    json_data = call_grpc(region, key, GRPC_DASHBOARD_METHOD)

    if not json_data:
        return

    for dashboard in json_data['items']:
        dashboards[dashboard['id']] = dashboard['name']

    print('number of dashboard added [{}]'.format(len(dashboards)))

    return dashboards


def send_enrichment(region, key, dictionary, enrichment_file_name):

    filename = "{}.csv".format(enrichment_file_name)
    f = open(filename, 'w')

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
            "file": (filename, open(filename,  'rb'))
    }

    enrichment_url = coralogix_custom_enrichment_url.format(region_domains[region],'','')
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
        files=files
    ))
    print(response)

    files['file'][1].close()

