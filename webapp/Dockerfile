FROM python:3.11.3-slim-buster
LABEL authors="sergej"

# Setting work directory
WORKDIR /usr/src/app

# Set envirable
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY .. /usr/src/app
