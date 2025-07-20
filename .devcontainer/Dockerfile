# Use Ubuntu with Python pre-installed
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=development
ENV PYTHON_ENV=development

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        curl \
        git \
        wget \
        unzip \
        software-properties-common \
        ca-certificates \
        gnupg \
        lsb-release \
        vim \
        nano \
        htop \
        tree \
        jq \
        redis-server \
    && apt-get autoremove -y && apt-get clean -y

# Install Node.js 18 (official repository)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install UV (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create vscode user and workspace
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user if it doesn't exist
RUN if ! id -u $USERNAME > /dev/null 2>&1; then \
        groupadd --gid $USER_GID $USERNAME \
        && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
        && apt-get update \
        && apt-get install -y sudo \
        && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
        && chmod 0440 /etc/sudoers.d/$USERNAME; \
    fi

# Install Playwright browsers (as vscode user)
USER $USERNAME
RUN npx playwright install-deps && npx playwright install

# Install UV for vscode user
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/$USERNAME/.cargo/bin:$PATH"

# Set up workspace directory
WORKDIR /workspace

# Copy package files for better caching
COPY package*.json ./
COPY pyproject.toml uv.lock* ./

# Install Node.js dependencies
RUN npm ci

# Install Python dependencies
RUN uv sync --dev || echo "UV sync will be completed in setup script"

# Install additional development tools
RUN npm install -g @vue/cli @electron/rebuild

# Create necessary directories
RUN mkdir -p /home/$USERNAME/.config/gh \
    && mkdir -p /workspace/.vscode \
    && mkdir -p /workspace/logs

# Set up Git configuration template
RUN git config --global init.defaultBranch main \
    && git config --global pull.rebase false \
    && git config --global --add safe.directory /workspace

# Expose ports for development
EXPOSE 8000 5173 3000 8080

# Set the default command
CMD ["bash"]