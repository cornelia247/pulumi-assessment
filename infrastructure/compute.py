import pulumi
import pulumi_aws as aws
from typing import Dict

class ComputeStack:
    def __init__(self, network, security, data, project_name: str, environment: str, common_tags: Dict[str, str]):
        self.project_name = project_name
        self.environment = environment
        self.network = network
        self.security = security
        self.data = data
        self.common_tags = common_tags
        
        # Create ECS cluster
        self.cluster = self.create_ecs_cluster()
        
        # Create ALB
        self.alb = self.create_application_load_balancer()
        self.elasticsearch_tg = self.create_target_group("elasticsearch", 9200)
        self.logstash_tg = self.create_target_group("logstash", 5044)
        self.kibana_tg = self.create_target_group("kibana", 5601)        
        self.listener = self.create_listener()

        self.listener_rules= self.create_listener_rules()
        
        # Create ECS task definition and service
        # self.task_definition = self.create_task_definition()
        # self.ecs_service = self.create_ecs_service()
        
        # Create Auto Scaling
        # self.create_auto_scaling()

    def create_ecs_cluster(self):
        try:
            return aws.ecs.Cluster(
                f"{self.project_name}-ecs-cluster",
                settings=[{
                    "name": "containerInsights",
                    "value": "enabled"
                }],
                tags=self.common_tags

            )
        except Exception as e:
            raise Exception(f"Failed to create ECS-cluter: {str(e)}")

    def create_application_load_balancer(self):
        try:
            alb = aws.lb.LoadBalancer(
                f"{self.project_name}-app-lb",
                internal=False,
                load_balancer_type="application",
                security_groups=[self.security.alb_security_group.id],
                subnets=self.network.public_subnet_ids,
                enable_deletion_protection=False, #Change to true in prod
                tags=self.common_tags,

            )
            return alb
        except Exception as e:
            raise Exception(f"Failed to create ALB: {str(e)}")
        

    def create_target_group(self, name, port, protocol="HTTP", health_path="/health"):
        try:
            return aws.lb.TargetGroup(
                f"{name}-tg",
                port=port,
                protocol=protocol,
                vpc_id=self.network.vpc.id,
                target_type="ip",  # ECS Fargate uses IP as targets
                health_check={
                    "enabled": True,
                    "healthy_threshold": 2,
                    "interval": 30,
                    "path": health_path,
                    "port": "traffic-port",
                    "protocol": protocol,
                    "timeout": 5,
                    "unhealthy_threshold": 2,
                    "matcher": "200"
                },
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create TargetGroup: {str(e)}")
        





    def create_listener(self):
        try:
            return aws.lb.Listener(
                f"{self.project_name}-app-listener",
                load_balancer_arn=self.alb.arn,
                port=80,
                protocol="HTTP",
                # ssl_policy="ELBSecurityPolicy-2016-08",
                # certificate_arn=self.security.ssl_certificate.arn,
                default_actions=[
                    {"type": "forward", "target_group_arn": self.kibana_tg.arn},  # Default points to Kibana
                ],
                tags=self.common_tags
            )
        except Exception as e:
            raise Exception(f"Failed to create ALB-listener: {str(e)}")
    
    def create_listener_rules(self):
        try:
            # Elasticsearch Rule
            elasticsearch_rule = aws.lb.ListenerRule(
                f"{self.project_name}-elasticsearch-rule",
                listener_arn=self.listener.arn,
                 conditions=[{
                    "path_pattern":{
                        "values":["/elasticsearch*"],
                    }
                }],
                actions=[{
                    "type": "forward",
                    "target_group_arn": self.elasticsearch_tg.arn
                }],
                priority=1  # Ensure unique priority
            )

            # Logstash Rule
            logstash_rule = aws.lb.ListenerRule(
                f"{self.project_name}-logstash-rule",
                listener_arn=self.listener.arn,
                conditions=[{
                    "path_pattern":{
                        "values":["/logstash*"],
                    }
                }],

                actions=[{
                    "type": "forward",
                    "target_group_arn": self.logstash_tg.arn
                }],
                priority=2
            )


            return [elasticsearch_rule, logstash_rule]
        except Exception as e:
            raise Exception(f"Failed to create ALB-listener-rules: {str(e)}")
   