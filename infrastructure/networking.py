import pulumi
import pulumi_aws as aws
from typing import Dict

class NetworkStack:
    def __init__(self, project_name: str, environment: str, common_tags: Dict[str, str]):
        self.project_name = project_name
        self.environment = environment
        self.common_tags = common_tags
        
        # Create VPC
        self.vpc = self.create_vpc()
        
        # Create Internet Gateway
        self.igw = self.create_internet_gateway()
        
        # Create subnets
        self.public_subnets = self.create_public_subnets()
        self.private_subnets = self.create_private_subnets()

        
        # Create NAT Gateways
        self.nat_gateways = self.create_nat_gateways()
        
        # Create route tables
        self.public_route_table = self.create_public_route_table()
        self.private_route_table = self.create_private_route_table()
        
        # Create Security Groups
        self.vpc_endpoint_security_group = self.create_vpc_endpoint_security_group()

        # Create Network ACLs
        # Create VPC endpoints
        self.vpc_endpoints = self.create_vpc_endpoints()

    def create_vpc(self):
        try:
            return aws.ec2.Vpc(
                f"{self.project_name}-vpc",
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-vpc"
                }
            )
        except Exception as e:
            raise Exception(f"Failed to create VPC: {str(e)}")

    def create_internet_gateway(self):
        try:
            igw = aws.ec2.InternetGateway(
            f"{self.project_name}-igw",
            vpc_id=self.vpc.id,
            tags={
                **self.common_tags,
                'Name': f"{self.project_name}-igw"
            }
            )
            return igw
        except Exception as e:
            raise Exception(f"Failed to create IGW: {str(e)}")

    def create_public_subnets(self):
        try:
            azs = aws.get_availability_zones(state="available").names
            public_subnets = []
        
            for i, az in enumerate(azs[:2]):
                subnet = aws.ec2.Subnet(
                    f"{self.project_name}-public-{az}",
                    vpc_id=self.vpc.id,
                    cidr_block=f"10.0.{i*2}.0/24",
                    availability_zone=az,
                    map_public_ip_on_launch=True,
                    tags={
                        **self.common_tags,
                        'Name': f"{self.project_name}-public-{az}",
                        'Type': 'Public'
                    }
                )
                public_subnets.append(subnet)
            
            return public_subnets
        
        except Exception as e:
            raise Exception(f"Failed to create PublicSubnet: {str(e)}")
        

    def create_private_subnets(self):
        try:
            azs = aws.get_availability_zones(state="available").names
            private_subnets = []
            
            for i, az in enumerate(azs[:2]):
                subnet = aws.ec2.Subnet(
                    f"{self.project_name}-private-{az}",
                    vpc_id=self.vpc.id,
                    cidr_block=f"10.0.{i*2+1}.0/24",
                    availability_zone=az,
                    tags={
                        **self.common_tags,
                        'Name': f"{self.project_name}-private-{az}",
                        'Type': 'Private'
                    }
                )
                private_subnets.append(subnet)
            
            return private_subnets
        except Exception as e:
            raise Exception(f"Failed to create PrivateSubnet: {str(e)}")


    def create_nat_gateways(self):
        try:
            eip = aws.ec2.Eip(
                f"{self.project_name}-nat-eip",
                domain="vpc",
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-nat-eip"
                }
            )
            
            nat_gateway = aws.ec2.NatGateway(
                f"{self.project_name}-nat",
                allocation_id=eip.id,
                subnet_id=self.public_subnets[0].id,  
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-nat"
                }
            )
            
            return nat_gateway
        except Exception as e:
            raise Exception(f"Failed to create NAT: {str(e)}")
    
    def create_public_route_table(self):
        try:
            route_table = aws.ec2.RouteTable(
                f"{self.project_name}-public-rt",
                vpc_id=self.vpc.id,
                routes=[
                    {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": self.igw.id,
                    }
                ],
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-public-rt"
                }
            )
            
            # Associate the public route table with the public subnets
            for i, subnet in enumerate(self.public_subnets):
                aws.ec2.RouteTableAssociation(
                    f"{self.project_name}-public-rt-assoc-{i}",
                    subnet_id=subnet.id,
                    route_table_id=route_table.id
                )
            
            return route_table
        except Exception as e:
            raise Exception(f"Failed to create PublicRouteTable: {str(e)}")
    

    def create_private_route_table(self):
        try:
            route_table = aws.ec2.RouteTable(
                f"{self.project_name}-private-rt",
                vpc_id=self.vpc.id,
                routes=[
                    {
                        "cidr_block": "0.0.0.0/0",
                        "nat_gateway_id": self.nat_gateways.id,
                    }
                ],
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-private-rt"
                }
            )
            
            # Associate the route table with all private subnets
            for i,  private_subnet in enumerate(self.private_subnets):
                aws.ec2.RouteTableAssociation(
                    f"{self.project_name}-private-rt-assoc-{i}",
                    subnet_id=private_subnet.id,
                    route_table_id=route_table.id
                )
            
            return route_table
        except Exception as e:
            raise Exception(f"Failed to create PrivateRouteTable: {str(e)}")



    def create_vpc_endpoint_security_group(self):
        try:
            return aws.ec2.SecurityGroup(
                f"{self.project_name}-vpce-sg",
                vpc_id=self.vpc.id,
                description="Security group for VPC endpoints",
                ingress=[{
                    'protocol': 'tcp',
                    'from_port': 443,
                    'to_port': 443,
                    'cidr_blocks': [self.vpc.cidr_block],
                }],
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-vpce-sg"
                }
            )
        except Exception as e:
            raise Exception(f"Failed to create VPCSecurityGroup {str(e)}")
    



    def create_vpc_endpoints(self):
        try:
            endpoints = {}
            
            # S3 Gateway Endpoint
            endpoints['s3'] = aws.ec2.VpcEndpoint(
                f"{self.project_name}-s3-endpoint",
                vpc_id=self.vpc.id,
                service_name=f"com.amazonaws.{aws.get_region().name}.s3",
                vpc_endpoint_type="Gateway",
                route_table_ids=[self.private_route_table.id],
                tags={
                    **self.common_tags,
                    'Name': f"{self.project_name}-s3-endpoint"
                }
            )
            
            # ECR Interface Endpoints
            for service in ['ecr.api', 'ecr.dkr']:
                endpoints[service] = aws.ec2.VpcEndpoint(
                    f"{self.project_name}-{service}-endpoint",
                    vpc_id=self.vpc.id,
                    service_name=f"com.amazonaws.{aws.get_region().name}.{service}",
                    vpc_endpoint_type="Interface",
                    subnet_ids=[subnet.id for subnet in self.private_subnets],
                    security_group_ids=[self.vpc_endpoint_security_group.id],
                    private_dns_enabled=True,
                    tags={
                        **self.common_tags,
                        'Name': f"{self.project_name}-{service}-endpoint"
                    }
                )
            
            return endpoints
        except Exception as e:
            raise Exception(f"Failed to create VPCEndpoints {str(e)}")

    @property
    def private_subnet_ids(self):
        return [subnet.id for subnet in self.private_subnets]

    @property
    def public_subnet_ids(self):
        return [subnet.id for subnet in self.public_subnets]