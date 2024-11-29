# infrastructure/monitoring.py
import pulumi
import pulumi_aws as aws
from typing import Dict

class MonitoringStack:
    def __init__(self, network, security, compute, project_name: str, environment: str, common_tags: Dict[str, str]):
        self.network = network
        self.security = security
        self.compute = compute
        self.common_tags = common_tags
        self.project_name = project_name
        self.environment = environment

        self.elasticsearch_task = self.create_elasticsearch_task()
        self.elasticsearch_service = self.create_elasticsearch_service()
        self.logstash_task = self.create_logstash_task()
        self.logstash_service = self.create_logstash_service()
        self.kibana_task = self.create_kibana_task()
        self.kibana_service = self.create_kibana_service()


        self.elasticsearch_autoscaling = self.create_auto_scaling(self.elasticsearch_service, "elasticsearch")
        self.logstash_autoscaling = self.create_auto_scaling(self.logstash_service, "logstash")
        self.kibana_autoscaling = self.create_auto_scaling(self.kibana_service, "kibana")
        


    def create_elasticsearch_task(self):
        try:
            return aws.ecs.TaskDefinition(f"{self.project_name}-elasticsearch-task",
                family="elasticsearch",
                network_mode="awsvpc",
                container_definitions=pulumi.Output.json_dumps([{
                    "name": "elasticsearch",
                    "image": "docker.elastic.co/elasticsearch/elasticsearch:8.10.0",
                    "memory": 1024,
                    "cpu": 512,
                    "environment": [
                        {"name": "discovery.type", "value": "single-node"},
                        {"name": "xpack.security.enabled", "value": "false"}
                    ],
                    "portMappings": [{"containerPort": 9200}],
                }]),
                requires_compatibilities=["FARGATE"],
                execution_role_arn=self.security.ecs_execution_role.arn,
                task_role_arn=self.security.ecs_task_role.arn,
                memory="2048",
                cpu="1024",
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create elasticsearch-task: {str(e)}")

    def create_elasticsearch_service(self):
        try:
            return aws.ecs.Service(f"{self.project_name}-elasticsearch-service",
                cluster=self.compute.cluster.id,
                task_definition=self.elasticsearch_task.arn,
                desired_count=2,
                launch_type="FARGATE",
                network_configuration={
                    "assign_public_ip": False,
                    "subnets": self.network.private_subnet_ids,
                    "security_groups": [self.security.ecs_security_group.id]
                },
                load_balancers=[{
                "target_group_arn": self.compute.elasticsearch_tg.arn,
                "container_name": "elasticsearch",
                "container_port": 9200
            }],
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create elasticsearch-service: {str(e)}")

    def create_logstash_task(self):
        try:

            return aws.ecs.TaskDefinition(
                f"{self.project_name}-logstash-task",
                family="logstash",
                cpu="256",
                memory="512",
                network_mode="awsvpc",
                requires_compatibilities=["FARGATE"],
                execution_role_arn=self.security.ecs_execution_role.arn,
                task_role_arn=self.security.ecs_task_role.arn,
                container_definitions=pulumi.Output.json_dumps([{
                "name": "logstash",
                "image": "docker.elastic.co/logstash/logstash:8.10.0",
                "memory": 512,
                "cpu": 256,
                "essential": True,
                "environment": [
                    {"name": "LS_JAVA_OPTS", "value": "-Xmx256m -Xms256m"},
                    {"name": "LOGSTASH_CONFIG_STRING", "value": """
                    input { beats { port => 5044 } }
                    filter { }
                    output {
                    elasticsearch {
                        hosts => ["http://elasticsearch:9200"]
                        index => "logstash-%{+YYYY.MM.dd}"
                    }
                    }
                    """}],
                    "portMappings": [{"containerPort": 5044}],
                }]),
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create logstash-task: {str(e)}")

    def create_logstash_service(self):
        try:
            return aws.ecs.Service(
                f"{self.project_name}-logstash-service",
                cluster=self.compute.cluster.id,
                desired_count=2,
                launch_type="FARGATE",
                task_definition=self.logstash_task.arn,
                network_configuration={
                    "assign_public_ip": False,
                    "subnets": self.network.private_subnet_ids,
                    "security_groups": [self.security.ecs_security_group.id]
                },
                load_balancers=[{
                "target_group_arn": self.compute.logstash_tg.arn,
                "container_name": "logstash",
                "container_port": 5044
            }],
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create logstash-service: {str(e)}")

    def create_kibana_task(self):
        try:
            return aws.ecs.TaskDefinition(f"{self.project_name}-kibana-task",
                family="kibana",
                network_mode="awsvpc",
                container_definitions=pulumi.Output.json_dumps([{
                    "name": "kibana",
                    "image": "docker.elastic.co/kibana/kibana:8.10.0",
                    "memory": 1024,
                    "cpu": 512,
                    "environment": [
                        {"name": "ELASTICSEARCH_HOSTS", "value": "http://elasticsearch:9200"}
                    ],
                    "portMappings": [{"containerPort": 5601}],
                }]),
                requires_compatibilities=["FARGATE"],
                execution_role_arn=self.security.ecs_execution_role.arn,
                task_role_arn=self.security.ecs_task_role.arn,
                memory="2048",
                cpu="1024",
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create kibana-task: {str(e)}")

    def create_kibana_service(self):
        try:
            return aws.ecs.Service(f"{self.project_name}-kibana-service",
                cluster=self.compute.cluster.id,
                task_definition=self.kibana_task.arn,
                desired_count=1,
                launch_type="FARGATE",
                network_configuration={
                        "assign_public_ip": False,
                        "subnets": self.network.private_subnet_ids,
                        "security_groups": [self.security.ecs_security_group.id]
                    },
                    load_balancers=[{
                    "target_group_arn": self.compute.kibana_tg.arn,
                    "container_name": "kibana",
                    "container_port": 5601
                }],
                tags=self.common_tags
                    
                )
        except Exception as e:
            raise Exception(f"Failed to create kibana-service: {str(e)}")
        


    def create_auto_scaling(self, service, name: str):
        try:
            target = aws.appautoscaling.Target(
                f"{self.project_name}-{name}-AS-target",
                max_capacity=5,
                min_capacity=1,
                resource_id=pulumi.Output.concat("service/", self.compute.cluster.name, "/", service.name),
                scalable_dimension="ecs:service:DesiredCount",
                service_namespace="ecs",
                tags=self.common_tags
                
            )

            # CPU-based scaling
            aws.appautoscaling.Policy(
                f"{name}-app-cpu-scaling",
                policy_type="TargetTrackingScaling",
                resource_id=target.resource_id,
                scalable_dimension=target.scalable_dimension,
                service_namespace=target.service_namespace,
                target_tracking_scaling_policy_configuration={
                    "predefined_metric_specification": {
                        "predefined_metric_type": "ECSServiceAverageCPUUtilization"
                    },
                    "target_value": 70.0,
                    "scale_in_cooldown": 60,
                    "scale_out_cooldown": 60
                }
            )

            # Memory-based scaling
            aws.appautoscaling.Policy(
                f"{name}-app-memory-scaling",
                policy_type="TargetTrackingScaling",
                resource_id=target.resource_id,
                scalable_dimension=target.scalable_dimension,
                service_namespace=target.service_namespace,
                target_tracking_scaling_policy_configuration={
                    "predefined_metric_specification": {
                        "predefined_metric_type": "ECSServiceAverageMemoryUtilization"
                    },
                    "target_value": 80.0,
                    "scale_in_cooldown": 100,
                    "scale_out_cooldown": 100
                }
            )
        except Exception as e:
            raise Exception(f"Failed to create auto-scaling: {str(e)}")



   
