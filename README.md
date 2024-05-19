# Coralogix python services

The python services include:
- **Coralogix artifact collector** (main.py)
- **L2Ms auto creation** (create_audit_l2m.py)
- **Delete APM services** (delete_apm_services.py)
- **Otel custom metrics sample** (custom_metrics.py)

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
        "key": "<team2 alerts api key>"
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
```
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

To simulate flushing the following environment variable is required
```shell
export simulate=true
```

The following python functions (provided in cx_infra.py) are being used:
- get_dashboards : get dashboards of a team for the enrichment file
- send_enrichment :  sending coralogix dashboards ID and their names to an audit account for enrichment

To send the enrichment file for the audit account the following environment variables are required:
```shell
export CX_API_KEY_REGION=<your our audit account region>
export CX_API_KEY=<your our audit alert key>
```

## L2Ms auto creation
The following python functions (provided in cx_infra.py) are being used:
- create_e2m : create l2m for Users (users activities), dashboards usage and dataprime queries usage

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
