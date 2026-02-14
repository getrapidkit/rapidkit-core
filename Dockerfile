# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.2.1 \
    DEBIAN_FRONTEND=noninteractive

# Install minimal system dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry (must be compatible with poetry.lock)
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Set work directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pyproject.toml poetry.lock README.md ./

# Configure poetry and install ONLY production dependencies
RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel true && \
    poetry install --only=main --no-interaction --no-ansi --no-root

# Copy source code
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Copy only essential runtime files
COPY assets/ ./assets/

# Create a simple entrypoint script
RUN printf '#!/bin/bash\nexec python -c "import sys; sys.path.insert(0, '\''/app/src'\''); from cli.main import main; main()" "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create non-root user and set permissions
RUN useradd --create-home --shell /bin/bash --uid 1000 rapidkit && \
    chown -R rapidkit:rapidkit /app

# Switch to non-root user
USER rapidkit

# Set Python path
ENV PYTHONPATH="/app/src"

# Default command
ENTRYPOINT ["/app/entrypoint.sh"]
