import json
from datetime import date, datetime
from typing import Any

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from .helpers import get_environment_variables
from .services import Service, ServiceEvent

db_client = boto3.client('rds')
ec2_client = boto3.client('ec2')
ecs_client = boto3.client('ecs')
service = Service(ec2_client)
SERVICE_NAME: str = ("Automated services")

logger = Logger(service=SERVICE_NAME)
metrics = Metrics(service=SERVICE_NAME)
tracer = Tracer(service=SERVICE_NAME)

EC2: str = "EC2"
ECS: str = "ECS"
RDS: str = "RDS"


# TODO: add logging
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@event_parser(model=ServiceEvent)
def lambda_handler(
        event: ServiceEvent,
        context: LambdaContext,
) -> dict[str, Any]:
    services = event.dict()
    env_vars = get_environment_variables()
    processing_time = datetime.now()
    services_started = []
    services_stopped = []

    for key, execute in services.items():
        if not execute:
            continue

        if key == EC2:
            service.strategy = ec2_client
        elif key == ECS:
            service.strategy = ecs_client
        else:
            service.strategy = db_client

        if date.today().weekday() in [5, 6]:
            if processing_time <= env_vars.weekend_start:
                service.start()
                services_started.append(key)

            if processing_time >= env_vars.weekend_end:
                service.stop()
                services_stopped.append(key)

        else:
            if processing_time <= env_vars.weekday_start:
                service.start()
                services_started.append(key)

            if processing_time >= env_vars.weekday_end:
                service.stop()
                services_stopped.append(key)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'servicesStopped': services_stopped,
        'servicesStarted': services_started,
        'processing_time': processing_time.isoformat(),
    }
