FROM python:3.7.4

ARG project_directory
WORKDIR $project_directory

RUN apt update
RUN apt install vim -y

COPY ./requirements.txt /app
RUN pip install -r requirements.txt