#!/bin/bash

# Step 1: Create a Dockerfile
cat > Dockerfile <<EOF
# Use the official Jupyter base image
FROM jupyter/base-notebook

# Install additional Python packages if needed
USER root
RUN pip install numpy pandas matplotlib

# Switch back to the non-root 'jovyan' user provided by the base image
USER jovyan

# Expose the port Jupyter will run on
EXPOSE 8888
EOF

# Step 2: Build the Docker Image
docker build -t my-jupyter-server .

# Step 3: Run the Docker Container
docker run -d --name my-jupyter-instance -p 8888:8888 \
  --restart always \
  -v /path/to/local/notebooks:/home/jovyan/work \
  my-jupyter-server

echo "Jupyter Server is running and available on port 8888 of the host machine."
