# Use an official Python runtime as a parent image, ensuring it's compatible with your project's Python version.
FROM python:3.12-slim

# Set environment variables to avoid Python buffering and enable unattended installation.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Add ~/.local/bin to PATH for pipx installed packages
ENV PATH="/root/.local/bin:${PATH}"
# Install system dependencies required for pyenv and other tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential
# Multiple RUN commands are used to take advantage of Docker's layer caching mechanism.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev 
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-dev \
    libpq-dev \
    wget \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev 
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    ca-certificates && \
    # Clean up apt cache to reduce image size.
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pipx.
RUN python -m pip install --upgrade pip && pip install pipx && pipx ensurepath

# Install Poetry via pipx.
RUN pipx install poetry

# Clone the project repository.
RUN git clone https://github.com/witzbeck/alexlib /alexlib

# Set the working directory to the cloned repository.
WORKDIR /alexlib

# Install project dependencies using Poetry.
RUN poetry install --with dev

# Expose a port
EXPOSE 8000
