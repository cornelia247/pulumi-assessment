# Security Overview

## Networking and ECS Infrastructure

**We designed our VPC architecture with security and scalability in mind.**  
The VPC spans across two availability zones for high availability and includes both private and public subnets. The private subnets house sensitive components like our ECS Fargate tasks and RDS instances, ensuring they are isolated from direct internet exposure. Public subnets are reserved for services like the Application Load Balancer (ALB), which manages inbound traffic securely.

- **NAT Gateway** was deployed to provide controlled outbound internet access for private subnets, allowing tasks to pull updates or communicate with external services while remaining isolated from inbound traffic.
- **Internet Gateway** is used to support public-facing services through the ALB. Route tables were configured to ensure traffic segregation, enforcing clear boundaries between public and private zones.
- **VPC endpoints** were implemented to enable secure, private connectivity to AWS services like S3 without requiring public internet access. This ensures our private resources communicate efficiently and securely within AWS's network.

The **ALB** is the only public-facing component. It uses HTTPS for secure communication, ensuring data in transit is encrypted. It is configured with security groups that restrict traffic to only necessary ports.

Our **ECS Fargate tasks** operate within private subnets, with their security groups allowing only traffic from the ALB and other authorized services. We also leverage IAM roles with the least privilege principle, ensuring each task has access only to the resources it needs. For scaling, we use auto-scaling groups to maintain performance while avoiding over-provisioning, keeping costs and potential attack surfaces minimal.

---

## Database Security

**For our database infrastructure, we prioritize encryption, access control, and fail-safe configurations.**  
Our Amazon RDS instance is a PostgreSQL database housed within a private subnet. This placement ensures it is inaccessible from the internet, further enhancing its security.

- **Automated backups** are enabled, ensuring that we have consistent and recoverable snapshots of our data, which are encrypted for security.
- **Encryption at rest** is managed with AWS KMS keys. These keys ensure that all stored data, including backups, is protected. By using KMS, we maintain centralized control over our encryption policies.
- **Database credentials** are securely stored in AWS Secrets Manager. This ensures that sensitive information is never hard-coded or exposed in our infrastructure. Secrets Manager also automates key rotation, reducing risks associated with stale or compromised credentials.

Our **subnet groups and parameter groups** for RDS are tailored to align with our availability and performance requirements. By leveraging subnet groups, we ensure the database is available across multiple zones, while parameter groups allow fine-tuned configurations specific to our workloads.

---

## Tagging Strategy

**We’ve implemented a detailed tagging strategy across all our resources.**  
This ensures that resources are consistently organized, easily identifiable, and that access controls are enforced at a granular level. Tags also facilitate auditing and cost management by allowing us to track ownership, environment (e.g., staging vs. production), and compliance requirements.