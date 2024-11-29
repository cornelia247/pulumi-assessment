import json
import pulumi
import pulumi_aws as aws
from typing import Dict

class DataStack:
    def __init__(self, network, security, config, project_name: str, rds_instance_class: str, rds_allocated_storage: int, environment: str, common_tags: Dict[str, str]):
        self.network = network
        self.security = security
        self.project_name = project_name
        self.environment = environment
        self.common_tags = common_tags
        self.config = config
        self.rds_allocated_storage= rds_allocated_storage
        self.rds_instance_class= rds_instance_class
        
        # Create subnet group
        self.db_subnet_group = self.create_db_subnet_group()
        
        # Create parameter group
        self.db_parameter_group = self.create_db_parameter_group()
        
        # Create RDS instance
        self.db_instance = self.create_db_instance()

    def create_db_subnet_group(self):
        try:
            return aws.rds.SubnetGroup(
                f"{self.project_name}-db-subnet-group",
                subnet_ids=self.network.private_subnet_ids,
                tags={
                            **self.common_tags,
                            'Name': f"{self.project_name}-db-subnet-group"
                        }
            )
        except Exception as e:
            raise Exception(f"Failed to create RDS-subnet-group: {str(e)}")

    def create_db_parameter_group(self):
        try:
            return aws.rds.ParameterGroup(
                f"{self.project_name}-db-parameter-group",
                family="postgres14",
                description="Custom parameter group for PostgreSQL 14",
                parameters=[
                    {
                    "name": "max_connections",
                    "value": "100",
                    "applyMethod": "pending-reboot",
                    },
                    {
                        "name": "shared_buffers",
                        "value": "16384",
                        "applyMethod": "pending-reboot",
                    },
                    {
                        "name": "log_statement",
                        "value": "all",
                        "applyMethod": "immediate",  
                    },
                ],
                tags={
                            **self.common_tags,
                            'Name': f"{self.project_name}-db-parameter-group"
                        }
            )
        except Exception as e:
            raise Exception(f"Failed to create RDS-parameter-group: {str(e)}")

    def create_db_instance(self):   
        try:
                # Fetch secret dynamically
            secret_id = self.security.db_secret.id
            secret_values = secret_id.apply(
                lambda id: aws.secretsmanager.get_secret_version_output(secret_id=id).secret_string
            )

            # Parse the username and password from the secret
            username = secret_values.apply(lambda s: json.loads(s)["username"])
            password = secret_values.apply(lambda s: json.loads(s)["password"])
            # Create RDS instance using the secret values
            return aws.rds.Instance(
                f"{self.project_name}-postgresql",
                allocated_storage=self.rds_allocated_storage,
                storage_type="gp2",
                engine="postgres",
                engine_version="14.12",
                instance_class=self.rds_instance_class,
                db_name=f"{self.project_name}_db",
                parameter_group_name=self.db_parameter_group.name,
                db_subnet_group_name=self.db_subnet_group.name,
                vpc_security_group_ids=[self.security.rds_security_group.id],
                storage_encrypted=True,
                kms_key_id=self.security.kms_key.arn,
                username=username,
                password=password,
                multi_az=True,
                publicly_accessible=False,
                backup_retention_period=7,
                backup_window="03:00-04:00",
                maintenance_window="Mon:04:00-Mon:05:00",
                auto_minor_version_upgrade=True,
                deletion_protection=False,  # Change to true in prod
                skip_final_snapshot=False,
                final_snapshot_identifier=f"{self.project_name}-final-snapshot",
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-postgresql"
                }
            )
        except Exception as e:
            pulumi.log.error(f"Error creating DB instance: {e}")
            raise
    