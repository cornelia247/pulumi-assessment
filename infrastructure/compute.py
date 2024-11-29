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
        self.elasticsearch_listener_rule = self.create_listener_rule(self.elasticsearch_tg, "elasticsearch",10)
        self.logstash_listener_rule = self.create_listener_rule(self.logstash_tg, "logstash",20)
        self.Kibana_listener_rule = self.create_listener_rule(self.kibana_tg,"kibana",30)

       

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
                target_type="ip", 
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
                tags=self.common_tags,
                default_actions=[
                    {
                        "type": "fixed-response",  # Default action if no rules match
                        "fixed_response": {
                            "statusCode": "404",
                            "contentType": "text/plain",
                            "messageBody": "Not Found",
                        },
                    }
                ],
            )
        
         
        except Exception as e:
            raise Exception(f"Failed to create ALB-listener: {str(e)}")


    def create_listener_rule(self, target_group, name=str, priority=int):
        try:
            # Add a new listener rule for path-based routing
            return aws.lb.ListenerRule(
                f"{self.project_name}-{name}-rule",
                listener_arn=self.listener.arn,
                conditions=[{
                    "path_pattern": {
                    "values": [f"/{name}*"],
                     },
                }],
                actions=[{
                    "type": "forward",
                    "forward": {
                        "targetGroups": [{
                            "arn": target_group.arn,
                            "weight": 1
                        }]
                    }
                }],
                priority=priority,  
            )
        except Exception as e:
            raise Exception(f"Failed to create ALB listener rule: {str(e)}")
  

        
    
   