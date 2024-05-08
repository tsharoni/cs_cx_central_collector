
from os import environ

import cx_central


if __name__ == '__main__':

    # Required api_key for enrichment
    cx_api_key = environ.get('CX_API_KEY')
    cx_api_key_region = environ.get('CX_API_KEY_REGION')

    if cx_api_key and cx_api_key_region:
        cx_central.create_e2m(
            region=cx_api_key_region,
            key=cx_api_key,
            name="dashboards_usage",
            description="",
            query="_exists_:action_details.operation.operation_payload.dashboardId",
            labels_list={"dashboard_name": "action_details.operation.operation_payload.dashboardId_enriched",
                         "username": "actor.username",
                         "team_name": "action.team_name",
                         "action": "action_details.operation.action"},
            permutation=30000
        )

        cx_central.create_e2m(
            region=cx_api_key_region,
            key=cx_api_key,
            name="Users",
            description="",
            query="_exists_:actor.username\\tAND\\tNOT\\tcoralogix.metadata.applicationName:/.*_audit/",
            labels_list={
                "dashboard_name": "action_details.operation.operation_payload.dashboardId_enriched",
                "username": "actor.username",
                "coralogix_team": "action.team_name",
                "action": "action_details.operation.action",
                "action_description": "action.description"},
            permutation=30000
        )

        cx_central.create_e2m(
            region=cx_api_key_region,
            key=cx_api_key,
            name="dataprime_usage",
            description="",
            query="action_details.operation.action:\\\"api\/v1\/dataprime\/query\\\"",
            labels_list={
                "username": "actor.username",
                "coralogix_team": "action.team_name",
                "action": "action_details.operation.action",
                "query": "action_details.operation.operation_payload.payload_string"},
            permutation=30000
        )
