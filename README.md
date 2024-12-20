# Coralogix python services

The python services include:
- **Coralogix artifact collector** (cx_collector.py)
- **L2Ms auto creation** (create_audit_l2m.py)
- **Delete APM services** (delete_apm_services.py)
- **Otel custom metrics sample** (custom_metrics.py)
- **rules group deployment** (rulesgroups_deployment.py)
- **audit and configuration dashboard** (audit_and_configuration_statistics.json)
- **dump artifcats (alerts, cx dashboards and grafana dashboards) to json files** (cx_dashboards_dump.py)
- **import artifact (alerts)** (cx_import.py)
- **export custom dashboard** (custom_dashboard_export.py)
- **deploy custom dashboard** (custom_dashbaord_deployment.py)

All services (beside custom metrics sample) requires a teams.json file which contains the following data:
```json
[
  {
    "account": "<account name>",
    "skip": false,
    "teams": [
      {
        "name": "<team1 name>",
        "region": "<region>",
        "key": "<team1 alerts api key>"
      },
      {
        "name": "<team2 name>",
        "region": "<region>",
        "key": "<team2 alerts api key>",
        "team_id": "<team id>(required to collect users from team)"
      }
    ]
  },
  {
    "account": "<account2 name>",
    "skip": false,
    "teams": [
      {
        "name": "<team name>",
        "region": "<region>",
        "key": "<team2 alerts api key>"
      }
    ]
  }
]
```

To launch a script the following environment variables are required:
```shell
export CX_TOKEN=<your audit account sending log api token>
export CX_ENDPOINT=https://ingress.<domain>:443
export account=<account name> 
export CX_USERS_TOKEN=<your token taken from your region cookies>
```
Note, if CX_TOKEN or CX_ENDPOINT are undefined, the otel provider is set to http://localhost:4317/,
the local agent collector (no need to provide a token)

The CX_USERS_TOKEN is optional , in case it is not defined, no collection of users set for the account will be taken

## prerequisites:
- Install grpcurl ```brew install grpcurl``` 
- Istall python OTEL libraries: 
```
pip3 install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http opentelemetry-instrumentation-flask opentelemetry-instrumentation-requests
pip3 install opentelemetry-exporter-otlp-proto-grpc
```
- all functions require a region and a key

## Coralogix artifacts collector
The coralogix artifact collector gathers information for an account from all teams defined and sent their results in cx_configuration guage metric

The following python functions (provided in cx_central.py) are being used:
- set_attributes : set cx_configuration main attributes (account and team)
- flush_alerts : reading all alerts for a team and flush to an (audit) account
- flush_webhooks :  reading all webhooks for a team and flush to an (audit) account
- flush_rules :  reading all rules groups and parsing rules for a team and flush to an (audit) account
- flush_tco_overrides :  reading all tco overrides for a team and flush to an (audit) account
- flush_grafana :  reading all grafana dashboards and their panels for a team and flush to an (audit) account
- flush_e2m :  reading all E2Ms for a team and flush to an (audit) account
- flush_tco : reading all TCO policies for a team and flush to an (audit) account
- flush_recording_rule:  reading all recording rules for a team and flush to an (audit) account
- flush_apm_services :  reading all APM services for a team and flush to an (audit) account
- flush_slo: reading all APM SLOs for a team and flush to an (audit) account
- flush_dashboards :  reading all Coralogix dashboards and their widgets for a team and flush to an (audit) account
- flush_views: reading all coralogix views for a team and flush to an (audit) account

To simulate flushing the following environment variable is required
```shell
export simulate=true
```

The following python functions (provided in cx_infra.py) are being used:
- get_dashboards : get dashboards of a team for the enrichment file
- get_views : get views of a team for the enrichment file
- send_enrichment :  sending coralogix dashboards ID or views ID and their names to an audit account for enrichment

To send the enrichment file for the audit account the following environment variables are required:
```shell
export CX_API_KEY_REGION=<your our audit account region>
export CX_API_KEY=<your our audit alert key>
```

There is not autoamtion to set the key for custom enrichments file. Therefore manually add keys to the following:
- <account>-dashboards: action_details.operation.operation_payload.dashboardId
- <account>-views: action_details.operation.operation_payload.queryDef.selectedViewId

## L2Ms auto creation
The following python functions (provided in cx_infra.py) are being used:
- create_e2m : create l2m for Users (users activities), dashboards usage , view usage and dataprime queries usage

## Delete APM services
The following python functions (provided in cx_infra.py) are being used:
- delete_apm_services : delete all APM services that matches a regex pattern

## Otel custom metrics sample
The following python classes (provided in cx_otel.py) are being used:
- CoralogixOtel : provider (Coralogix endpoint)
  - init : to initiate provider with endpoint and key
- CoralogixOtelGauge : Gauge metric
  - init: to name the gauge metric
  - set_meta_attributes: to define the main attributes for the metric
  - flush results : to flush the gauge metrics with labels and result value
- cx_otel.CoralogixCounter : Counter metric
  - init: to name the counter metric
  - set_meta_attributes: to define the main attributes for the metric
  - flush results : to flush the counter metrics with labels and the increased value

To simulate flushing the following environment variable is required
```shell
export simulate=true
```

## Rules groups deployment
The following python functions (provided in cx_infra.py) are being used:
- get_rules: get all rules groups from a Coralogix team
- parse_rules: parse selected rules groups to a Coralogix team

## audit and configuration dashboard
The dashboard visualizes the data collected by the **coralogix collector** and the **L2Ms auto creation**

## dump artifcats
The following python functions (provided in cx_infra.py) are being used:
- get_dashboards: get all cx dashboards for a Coralogix team
- get_dashboard_file: get the json file of a dashboard
- get_grafana_dashboards: get all grafana dashboards for a Coralogix team
- get_grafana_dashboards_file: get the json file of a grafana dashboard
- get_alerts: get the alerts to a file
The account environment value is required to loop over the account's team

## import artifcats
The following python functions (provided in cx_infra.py) are being used:
- create_alert: create an alert on a Coralogix team
The script is based on the alerts json file exported from the dump artifacts script
The CX_API_KEY and the CX_API_KEY_REGION are required to import the alerts

<br>The script requires the following parameters:
```shell
python3 cx_import.py --alert_file_name <alert file name>.json --alert_name <regex for the alert name>
```
## custom dashboard export
The following python functions (provided in cx_infra.py) are being used:
 - get_dashboards: get all cx dashboards for a Coralogix team
 - get_dashboard_file: get the json file of a dashboard to a mako (template) file

<br>The script requires the following parameters:
```shell
python3 custom_dashboard_export.py --dashboard "<dashboard name>" --region <team region> --key <team key with dashboard read access>
```
## deploy dashboard export
The following pyhon functions (provided in cx_infra.py) are being used:
 - get_dashboards: get all cx dashboards for a Coralogix team
 - create_dashboard: create a new dashboard from a json file on a coralogix account if dashboard cannot be found
 - replace_dashboard: replace an existing dashboard with a new one

<br>The script requires the following parameters:
```shell
python3 custom_dashboard_deployment.py --dashboard_file <dashboard template file> --account <account name as defined in teams.json> --params <list of key-value pairs for template as unit_price=1.00>
```
This script requires a dashboard template file to allow replacing variables inside the template that requires to this deployment
In this example , the `unit_price` value `1.00` from the params would replace the `${unit_price}` in the template before deployment: 
```json lines
"value": "avg_over_time(sum(max_over_time(cx_data_usage_units{tier=\"high\",pillar=\"logs\",application_name=~\"{{application_name}}\",subsystem_name=~\"{{subsystem_name}}\"}[24h]))[${__range}:1h])*${unit_price}"
```
Special placeholder added is `${team_name}` that replaces the placeholder with the coralogix team name as specified in the teams.json file:
```json lines
    "name": "[Coralogix] ${team_name} Data Usage and Cost estimate",
```