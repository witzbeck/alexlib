FROM ubuntu:latest

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Docker Compose version
ARG COMPOSE_VERSION=1.29.2

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    git \
    jq \
    docker.io \
    && curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Create a user for the runner
RUN useradd -m runner && \
    usermod -aG sudo runner && \
    usermod -aG docker runner && \
    echo runner ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/runner && \
    chmod 0440 /etc/sudoers.d/runner

# Download and configure the GitHub Actions runner
ARG RUNNER_VERSION="2.283.1"
RUN curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -C /home/runner && \
    rm ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    chown -R runner:runner /home/runner

USER runner
WORKDIR /home/runner

COPY entrypoint.sh .
RUN sudo chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
