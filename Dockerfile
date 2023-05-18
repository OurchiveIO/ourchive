# Dockerfile

# pull base image
FROM python:3.7

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code
COPY . /code/


# Install dependencies
#RUN pip install pipenv
RUN pip install -r requirements.txt
#COPY Pipfile Pipfile.lock /code/
#RUN pipenv install --system


