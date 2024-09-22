# Use an official Python runtime as a parent image
FROM quay.io/jupyter/base-notebook:latest

# install dependancies
USER root
RUN apt-get update && apt-get install -y \
git git-lfs \
build-essential \
cmake \
libpq-dev \
python3-dev

RUN apt-get clean && \
rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

# Install the required libraries for your notebook
RUN pip3 install -U --no-cache-dir -r /tmp/requirements.txt
# RUN pip3 install -U --no-cache-dir -e .

# set PATH
ENV PATH=/root/.local/bin:$PATH

COPY . /home/jovyan/work

WORKDIR /home/jovyan/work

# Expose the port used by Kernel
EXPOSE 8888
