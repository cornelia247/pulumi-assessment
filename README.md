# **Numeris Infrastructure Project**

## **Overview**
This project provisions and manages a secure and scalable infrastructure on AWS using **Pulumi**, with key components deployed on **AWS Fargate**, **Amazon RDS**, and **Elastic Load Balancer (ALB)**. The project is optimized for cost-effectiveness and reliability, supporting an Elasticsearch stack (Elasticsearch, Logstash, and Kibana).

---

## **Key Features**
- **Networking**:
  - VPC with public and private subnets across multiple availability zones.
  - NAT Gateway and Internet Gateway for secure traffic routing.

- **Compute**:
  - ECS Fargate tasks for Elasticsearch, Logstash, and Kibana.
  - Auto-scaling configured to maintain performance and reduce costs.

- **Database**:
  - Amazon RDS for PostgreSQL with Multi-AZ deployment and automated backups.
  - Encrypted storage and secrets managed via AWS Secrets Manager.

- **Load Balancing**:
  - Application Load Balancer (ALB) for secure traffic distribution to Fargate tasks.

---

## **Cost Analysis**
- **Monthly Estimate**: **$356.40**
  - RDS: $181.90/month
  - ECS Fargate: $100.65/month
  - ALB: $39.79/month
  - NAT Gateway: $33.30/month
  - Secrets Manager: $0.76/month

---

## **Deployment**
1. **State Management**:
   - Pulumi state stored securely in **Amazon S3** with versioning and encryption.

2. **Pulumi Commands**:
   - Preview infrastructure:  
     ```bash
     pulumi preview
     ```
   - Deploy infrastructure:  
     ```bash
     pulumi up
     ```
   - Destroy infrastructure:  
     ```bash
     pulumi destroy
     ```

3. **AWS CLI for S3 Backend**:
   - S3 bucket configured for storing Pulumi state files with encryption and versioning.

---

## **Project Structure**
```plaintext
├── Pulumi.yaml         # Pulumi project metadata
├── Pulumi.dev.yaml     # Development stack configuration
├── Pulumi.prod.yaml    # Production stack configuration
├── requirements.txt    # Python dependencies
├── __main__.py         # Main Pulumi script
├── stacks/
│   ├── network.py      # Networking resources
│   ├── compute.py      # ECS Fargate tasks
│   └── data.py         # RDS and Secrets Manager
```
## **Acknowledgments**

This project was built using Pulumi for Infrastructure as Code (IaC) and AWS Services for hosting and security. Cost estimates are generated using the AWS Pricing Calculator.
