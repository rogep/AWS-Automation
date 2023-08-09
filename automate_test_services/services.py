from abc import ABC, abstractclassmethod

from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2 import ECSClient
from mypy_boto3_rds import RDSClient
from pydantic import BaseModel


class ServiceEvent(BaseModel):
    ec2: bool
    ecs: bool
    rds: bool
    # ecs_count: list[int] | None  # TODO: implement


class AWSStrategy(ABC):

    @abstractclassmethod
    def stop_services(self) -> None:
        pass

    # *args, **kwargs is for future implementation to extend ecs
    @abstractclassmethod
    def start_services(self, *args, **kwargs) -> None:
        pass


class RDS(AWSStrategy):
    def __init__(
            self,
            client: RDSClient,
    ) -> None:
        self._client = client
        self._clusters = self._get_clusters()

    def stop_services(self) -> None:
        for cluster in self._clusters:
            cluster_name = cluster['DBClusterIdentifier']
            self._client.stop_db_cluster(DBClusterIdentifier=cluster_name)

    def start_services(self) -> None:
        for cluster in self._clusters:
            cluster_name = cluster['DBClusterIdentifier']
            self._client.start_db_cluster(DBClusterIdentifier=cluster_name)

    def _get_clusters(self) -> list[dict[str, str]]:
        clusters = self._client.describe_db_clusters()
        return clusters['DBClusters']


class EC2(AWSStrategy):
    def __init__(
            self,
            client: EC2Client,
    ) -> None:
        self._client = client
        self._instance_ids = self._get_instance_ids()

    def stop_services(self) -> None:
        if len(self._instance_ids) > 0:
            self._client.stop_instances(InstanceIds=self._instance_ids)

    def start_services(self) -> None:
        if len(self._instance_ids) > 0:
            self._client.start_instances(InstanceIds=self._instance_ids)

    def _get_instance_ids(self) -> list[str]:
        response = self._client.describe_instances()
        instances = response['Reservations']
        if instances > 0:
            instance_ids = [id for id in instances['Instances']['InstanceId']]
        else:
            instance_ids = []
        return instance_ids


class ECS(AWSStrategy):
    def __init__(
            self,
            client: ECSClient,
    ) -> None:
        self._client = client
        self._metadata = self._get_service_metadata()

    def stop_services(self) -> None:
        for cluster, service in self._metadata:
            self._client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=0,
            )

    # TODO: make this accept a list of counts (if counts > 1 for some services)
    def start_services(self) -> None:
        for cluster, service in self._metadata:
            self._client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=1,
            )

    def _get_service_metadata(self) -> list[list[str]]:
        """Extract cluster and service names from
           arn:aws:ecs:<region>:<acc-id>:service/<cluster>/<service>"""
        response = self._client.list_services()
        # if no cluster is defined, then we get a ClusterNotFoundException
        metadata = [x.split['/'][1:] for x in response['clusterArns']]
        return metadata


class Service:
    def __init__(
            self,
            strategy: AWSStrategy
    ) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> AWSStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: AWSStrategy) -> None:
        self._strategy = strategy

    def start(self) -> None:
        self._strategy.start_services()

    def stop(self) -> None:
        self._strategy.stop_services()
