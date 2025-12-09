#!/bin/bash

# Build script for SaturdayMorningPlex
# This script builds and optionally pushes the Docker image

set -e

# Configuration
IMAGE_NAME="saturdaymorningplex"
VERSION="1.0.0"
DOCKER_USERNAME="${DOCKER_USERNAME:-yourdockerhub}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building SaturdayMorningPlex Docker Image${NC}"
echo "============================================"

# Build the image
echo -e "\n${YELLOW}Building image...${NC}"
docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${VERSION} .

echo -e "${GREEN}✓ Image built successfully${NC}"

# Tag for Docker Hub
echo -e "\n${YELLOW}Tagging image for Docker Hub...${NC}"
docker tag ${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker tag ${IMAGE_NAME}:${VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo -e "${GREEN}✓ Image tagged${NC}"

# Ask if user wants to push
echo -e "\n${YELLOW}Do you want to push to Docker Hub? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${YELLOW}Logging in to Docker Hub...${NC}"
    docker login
    
    echo -e "\n${YELLOW}Pushing images...${NC}"
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
    
    echo -e "${GREEN}✓ Images pushed successfully${NC}"
    echo -e "\nYour image is now available at:"
    echo -e "  ${GREEN}docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:latest${NC}"
else
    echo -e "\n${YELLOW}Skipping push to Docker Hub${NC}"
fi

echo -e "\n${GREEN}Build complete!${NC}"
echo -e "\nTo run locally:"
echo -e "  ${GREEN}docker run -d -p 5000:5000 --name ${IMAGE_NAME} ${IMAGE_NAME}:latest${NC}"
echo -e "\nOr use docker-compose:"
echo -e "  ${GREEN}docker-compose up -d${NC}"
