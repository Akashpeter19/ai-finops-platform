# Brain-Tasks-App

## Overview

This repository contains the Brain-Tasks-App deployment project completed using an AWS DevOps CI/CD workflow.

The application was deployed using:

- GitHub  
- AWS CodePipeline  
- AWS CodeBuild  
- Docker  
- Amazon ECR  
- Amazon EKS

## Repository Contents

- `Dockerfile` \- Packages the application using `nginx:alpine`  
- `buildspec.yml` \- Build instructions used by AWS CodeBuild  
- `deployment.yaml` \- Kubernetes deployment manifest  
- `service.yaml` \- Kubernetes service manifest  
- `screenshots/` \- Submission screenshots showing each stage of the project  
- `README.md` \- Project summary and setup explanation

## CI/CD Pipeline Flow

1. Source stage pulls code from the GitHub `main` branch.  
2. Build stage uses AWS CodeBuild to:  
   - authenticate with DockerHub and Amazon ECR  
   - build the Docker image  
   - tag the image  
   - push the image to Amazon ECR  
3. Deploy stage applies the Kubernetes deployment and service configuration to Amazon EKS.

## Docker Setup

The application uses the following Docker approach:

- Base image: `nginx:alpine`  
- Static build folder copied into `/usr/share/nginx/html`  
- Container exposed on port `80`

## AWS Resources Used

- **AWS Region:** `ap-south-1`  
- **ECR Repository:** `brain-tasks-app`  
- **EKS Cluster:** `eks-brain-tasks-cluster`  
- **Pipeline Name:** `brain-tasks-pipeline`  
- **Build Project:** `brain-tasks-build`

## Kubernetes Setup

- Deployment name: `brain-tasks-deployment`  
- Replicas: `2`  
- Service name: `brain-tasks-service`  
- Service type: `LoadBalancer`

## Setup / Verification Steps

### Build and push image

The image is built and pushed automatically through CodeBuild using `buildspec.yml`.

### Deploy to EKS

The Kubernetes resources are applied using:

kubectl apply \-f deployment.yaml

kubectl apply \-f service.yaml

### Verify deployment

kubectl get pods

kubectl get svc

## Submission Proof

The `screenshots/` folder contains ordered screenshots for:

- GitHub repository  
- Dockerfile and buildspec  
- Amazon ECR repository  
- CodeBuild success  
- CodePipeline overview and execution  
- EKS deployment proof  
- Application running in browser  
- Logs and pipeline trigger test

## Application Access

- **LoadBalancer URL:** http://a619664b33fd64b77a3ea38344c669a3-1958726347.ap-south-1.elb.amazonaws.com/  
- **LoadBalancer ARN:** arn:aws:eks:ap-south-1:145713875816:cluster/eks-brain-tasks-cluster

## Project Outcome

This project successfully demonstrates a complete CI/CD workflow from GitHub to AWS EKS using Docker, Amazon ECR, AWS CodeBuild, and AWS CodePipeline.  
