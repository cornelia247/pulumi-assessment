import pulumi
import pulumi_aws as aws
from infrastructure.networking import NetworkStack
from infrastructure.compute import ComputeStack
from infrastructure.data import DataStack
from infrastructure.security import SecurityStack
from infrastructure.monitoring import MonitoringStack

class MainStack:
    def __init__(self):
        # Stack configuration
        config = pulumi.Config()
        self.project_name = config.require('project')
        self.environment = config.require('environment')
        self.domain = config.require('domain')
        self.rds_instance_class = config.require('rds_instance_class')
        self.rds_allocated_storage = config.require('rds_allocated_storage')
        
        # Common tags for all resources
        self.common_tags = {
            'Project': self.project_name,
            'Environment': self.environment,
            'ManagedBy': 'Pulumi',
            'Owner': 'DevOps'
        }
        
        # Initialize stacks
        try:
            # Networking
            self.network = NetworkStack(
                project_name=self.project_name,
                environment=self.environment,
                common_tags=self.common_tags,
            )
            pulumi.log.debug("Network stack initialized successfully.")

            # Security
            self.security = SecurityStack(
                project_name=self.project_name,
                environment=self.environment,
                network=self.network, 
                common_tags=self.common_tags,
                domain=self.domain
            )
            pulumi.log.debug("Security stack initialized successfully.")

            # Data
            self.data = DataStack(
                network=self.network,
                project_name=self.project_name,
                environment=self.environment,
                security=self.security, 
                common_tags=self.common_tags,
                config=config,
                rds_instance_class=self.rds_instance_class,
                rds_allocated_storage = self.rds_allocated_storage
            )
            pulumi.log.debug("Data stack initialized successfully.")

            # Compute
            self.compute = ComputeStack(
                network=self.network,
                security=self.security,
                data=self.data,
                project_name=self.project_name,
                environment=self.environment,
                common_tags=self.common_tags,
            )
            pulumi.log.debug("Compute stack initialized successfully.")

            # Monitoring
            self.monitoring = MonitoringStack(
                network=self.network,
                security=self.security,
                compute=self.compute,
                project_name=self.project_name,
                environment=self.environment,
                common_tags=self.common_tags,
            )
            pulumi.log.debug("Monitoring stack initialized successfully.")

        except Exception as e:
            pulumi.log.error(f"Error initializing stacks: {str(e)}")
            raise

# Create main stack
main_stack = MainStack()

# Export important values
pulumi.export('vpc_id', main_stack.network.vpc.id)
pulumi.export('private_subnet_ids', main_stack.network.private_subnet_ids)
pulumi.export('public_subnet_ids', main_stack.network.public_subnet_ids)
pulumi.export('ecs_cluster_name', main_stack.compute.cluster.name)
pulumi.export('rds_endpoint', main_stack.data.db_instance.endpoint)
