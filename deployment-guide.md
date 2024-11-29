# Pulumi Infrastructure Deployment Guide

## Overview

This guide details how to deploy infrastructure using Pulumi with **Amazon S3** as the backend for state management. By centralizing the state file in S3, the deployment becomes more collaborative, consistent, and secure.

---

## Prerequisites

### Environment Setup

1. **AWS CLI**:
   - Install the AWS CLI:  

     ```bash
     curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
     unzip awscliv2.zip
     sudo ./aws/install
     ```

   - Configure AWS CLI credentials:

     ```bash
     aws configure
     ```

     Provide your `AWS Access Key ID`, `Secret Access Key`, and default region (e.g., `us-east-1`).

2. **Pulumi CLI**:
   - Install the Pulumi CLI:

     ```bash
     curl -fsSL https://get.pulumi.com | sh
     ```

3. **Python**:
   - Install Python (version 3.11 or compatible) and `pip`.

4. **Environment Variables**:
   Export Pulumi’s passphrase for managing encrypted secrets:

   ```bash
   export PULUMI_CONFIG_PASSPHRASE="your-secure-passphrase"
   ```

5. **Install Pulumi Dependencies**:

    - Create a requirements.txt file:

    ```bash
    pulumi>=3.0.0
    pulumi-aws>=5.0.0

    ```

    - Create a requirements.txt file:

    ``` bash
    pip install -r requirements.txt

    ```

## Step 1: Create an S3 Bucket for Pulumi State

To use S3 as Pulumi’s backend, create a dedicated bucket for state storage.

### Bucket Creation Using AWS CLI

1. **Create the bucket**:

    ``` bash
        aws s3api create-bucket \
    --bucket my-pulumi-state-bucket \
    --region <aws-region> 
    ```

2. **Enable versioning for the bucket**:

    ``` bash
        aws s3api put-bucket-versioning \
    --bucket my-pulumi-state-bucket \
    --versioning-configuration Status=Enabled
    ```

3. **Set encryption for the bucket**:

    ``` bash
        aws s3api put-bucket-encryption \
    --bucket my-pulumi-state-bucket \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
    ```

4. **Verify the bucket configuration**:

    ``` bash
        aws s3api get-bucket-encryption --bucket my-pulumi-state-bucket
    ```

## Step 2: Configure Pulumi to Use S3 as Backend

1. **Login to Pulumi with the S3 backend**:

    ``` bash
        pulumi login s3://my-pulumi-state-bucket'
    ```

2. **Verify that the backend is set to S3**:

    ``` bash
        pulumi whoami
    ```

## Step 3: Deploy Infrastructure

### Initialize the Pulumi Project

1. **Create a new Pulumi project**:

    ``` bash
        pulumi new aws-python
    ```

2. **Configure the stack**:

    ``` bash
        pulumi config set aws:region <aws-region>
    ```

### Preview Changes

- Preview the resources that will be created or updated:

    ``` bash
        pulumi preview
    ```

### Deploy Resources

- Deploy the stack:

    ``` bash
        pulumi up
    ```

## Step 4: Monitor State and Resources  

### View Pulumi State

1. **List stacks**:

    ``` bash
        pulumi stack ls
    ```

2. **Export current state**:

    ``` bash
        pulumi stack export > stack.json
    ```

## Step 5: Cleanup

- When resources are no longer needed, destroy them to avoid incurring charges:

    ``` bash
        pulumi destroy
    ```

- If the project is no longer required, remove the stack:

    ``` bash
        pulumi stack rm
    ```