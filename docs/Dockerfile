# ==========================================================
# GRIDTRUST
# Docker Image
#
# Builds a reproducible environment for the complete
# forecasting pipeline.
# ==========================================================

# base python image
FROM python:3.11-slim

# prevents python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# prints logs immediately
ENV PYTHONUNBUFFERED=1

# working directory inside container
WORKDIR /app

# installs system packages required by psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

#  dependency list
COPY requirements.txt .

# install python dependencies
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# copy entire project
COPY . .

# default command
CMD ["python", "src/automation/pipeline.py"]