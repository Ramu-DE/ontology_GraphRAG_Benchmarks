#!/bin/bash
# Install Python and dependencies on EC2 instance

echo "Installing Python and pip..."
sudo yum install -y python3-pip git

echo "Installing Python packages..."
sudo pip3 install gremlinpython opensearch-py requests-aws4auth boto3

echo "Installation complete!"
python3 --version
pip3 list | grep -E "gremlin|opensearch|boto3"
