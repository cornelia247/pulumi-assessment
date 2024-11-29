import pulumi
import pulumi_aws as aws
from typing import Dict
import json
import pulumi_random as random


class SecurityStack:
    def __init__(self, network,project_name: str, environment: str, common_tags: Dict[str, str], domain: str):
        self.network = network
        self.project_name = project_name
        self.environment = environment
        self.common_tags = common_tags
        self.domain = domain
        
        # Create KMS keys
        self.kms_key = self.create_kms_key()
        
        # Create security groups
        self.alb_security_group = self.create_alb_security_group()
        self.ecs_security_group = self.create_ecs_security_group()
        self.rds_security_group = self.create_rds_security_group()
        # self.es_security_group = self.create_elasticsearch_security_group()
        
        # Create IAM roles
        self.ecs_task_role = self.create_ecs_task_role()
        self.ecs_execution_role = self.create_ecs_execution_role()
        
        # Create SSL certificate
        # self.ssl_certificate = self.create_ssl_certificate()
        
        # Create secrets
        self.db_secret = self.create_db_secret()

    def create_kms_key(self):
        try:
            key_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{aws.get_caller_identity().account_id}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                }]
            }
            
            key = aws.kms.Key(
                f"{self.project_name}-kms-key",
                description=f"KMS key for {self.project_name}",
                deletion_window_in_days=7,
                enable_key_rotation=True,
                policy=json.dumps(key_policy),
                tags=self.common_tags
            )
            
            aws.kms.Alias(
                f"{self.project_name}-kms-alias",
                name=f"alias/{self.project_name}-key",
                target_key_id=key.id
            )
            
            return key
        except Exception as e:
            raise Exception(f"Failed to create KMS-Key: {str(e)}")

    def create_alb_security_group(self):
        try:
            return aws.ec2.SecurityGroup(
                f"{self.project_name}-alb-sg",
                vpc_id=self.network.vpc.id,
                description="Security group for Application Load Balancer",
                ingress=[
                    {
                        "protocol": "tcp",
                        "from_port": 80,
                        "to_port": 80,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "HTTP"
                    },
                    {
                        "protocol": "tcp",
                        "from_port": 443,
                        "to_port": 443,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "HTTPS"
                    }
                ],
                egress=[{
                    "protocol": "-1",
                    "from_port": 0,
                    "to_port": 0,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "description": "Allow all outbound traffic"
                }],
                tags={
                        **self.common_tags,
                        'Name': f"{self.project_name}-alb-sg"
                    }
            )
        except Exception as e:
            raise Exception(f"Failed to create ALB-SG: {str(e)}")

    def create_ecs_security_group(self):
        try:
            return aws.ec2.SecurityGroup(
                f"{self.project_name}-ecs-sg",
                vpc_id=self.network.vpc.id,
                description="Security group for ECS tasks",
                ingress=[
                    # Allow traffic on port 9200 for Elasticsearch
                    {
                        "protocol": "tcp",
                        "from_port": 9200,
                        "to_port": 9200,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "Allow Elasticsearch port"
                    },
                    # Allow traffic on port 5601 for Kibana
                    {
                        "protocol": "tcp",
                        "from_port": 5601,
                        "to_port": 5601,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "Allow Kibana port"
                    },
                    # Allow traffic on port 5044 for Logstash
                    {
                        "protocol": "tcp",
                        "from_port": 5044,
                        "to_port": 5044,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "Allow Logstash port"
                    },
                    # Optionally, allow HTTP (80) and HTTPS (443) traffic if needed
                    {
                        "protocol": "tcp",
                        "from_port": 80,
                        "to_port": 80,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "Allow HTTP traffic"
                    },
                    {
                        "protocol": "tcp",
                        "from_port": 443,
                        "to_port": 443,
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": "Allow HTTPS traffic"
                    }
                ],
                egress=[{
                    # Allow all outbound traffic
                    "protocol": "-1",
                    "from_port": 0,
                    "to_port": 0,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "description": "Allow all outbound traffic"
                }],
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-ecs-sg"
                }
            )
        except Exception as e:
            raise Exception(f"Failed to create ECS-SG: {str(e)}")

    def create_rds_security_group(self):
        try:
            return aws.ec2.SecurityGroup(
                f"{self.project_name}-rds-sg",
                vpc_id=self.network.vpc.id,
                description="Security group for RDS instance",
                ingress=[{
                    "protocol": "tcp",
                    "from_port": 5432,
                    "to_port": 5432,
                    "security_groups": [self.ecs_security_group.id],
                    "description": "Allow PostgreSQL access from ECS tasks"
                }],
                tags={
                        **self.common_tags,
                        'Name': f"{self.project_name}-rds-sg"
                    }
            )
        except Exception as e:
            raise Exception(f"Failed to create RDS-SG: {str(e)}")


    def create_ecs_task_role(self):
        try:
            role = aws.iam.Role(
                f"{self.project_name}-ecs-task-role",
                assume_role_policy="""{
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": "sts:AssumeRole",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Effect": "Allow"
                    }]
                }""",
                tags=self.common_tags
            )
        
            aws.iam.RolePolicy(
                f"{self.project_name}-ecs-task-policy",
                role=role.id,
                policy="""{
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": [
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Effect": "Allow",
                        "Resource": "arn:aws:logs:*:*:*"
                    }]
                }""")

            
            return role
        except Exception as e:
            raise Exception(f"Failed to create ECS-task-role: {str(e)}")

    def create_ecs_execution_role(self):
        try:

            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    }
                }]
            }
            
            role = aws.iam.Role(
                f"{self.project_name}-ecs-execution-role",
                assume_role_policy=json.dumps(assume_role_policy),
                tags=self.common_tags
            )
            
            aws.iam.RolePolicyAttachment(
                f"{self.project_name}-ecs-execution-policy",
                role=role.id,
                policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
            )
            
            return role
        except Exception as e:
            raise Exception(f"Failed to create ECS-execution-role: {str(e)}")

    # def create_ssl_certificate(self):


    #     try:
    #         # For development, you might want to use a self-signed certificate
    #         # For production, you should use AWS Certificate Manager with a valid domain
    #         certificate = aws.acm.Certificate(
    #             f"{self.project_name}-ssl-cert",
    #             domain_name=self.domain,
    #             validation_method="DNS",
    #             opts=pulumi.ResourceOptions(ignore_changes=["domain_validation_options"]),
    #             tags=self.common_tags
    #         )
            
    #         return certificate
    #     except Exception as e:
    #         raise Exception(f"Failed to create SSL-cert: {str(e)}")
    

    def create_db_secret(self):
        try:
            password = random.RandomPassword(
                "db-password",
                length=32,
                special=False
            )
            secret = aws.secretsmanager.Secret(
                f"{self.project_name}-db-secret",
                description="RDS database credentials",
                kms_key_id=self.kms_key.id,
                tags=self.common_tags
            )
            
            aws.secretsmanager.SecretVersion(
                f"{self.project_name}-db-secret-version",
                secret_id=secret.id,
                secret_string=password.result.apply(lambda pwd: json.dumps({
                    "username": "dbadmin",
                    "password": pwd
                }))
                )
            
            
            return secret
        except Exception as e:
            raise Exception(f"Failed to create DB-secret: {str(e)}")