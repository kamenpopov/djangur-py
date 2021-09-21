# syntax = docker/dockerfile:experimental

# This file is a template, and might need editing before it works on your project.
FROM python:3.6

WORKDIR /usr/local/djangur

# COPY requirements.txt ~/djangur
# RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/local/djangur
# COPY /usr/local/config.json /usr/local/djangur
# CMD ["pwd"]
# CMD ["ls"]

# CMD touch /usr/local/config.json

# CMD cp /usr/local/config.json /usr/local/djangur/config.json

RUN pip3 install -r requirements.txt

RUN touch config.json
RUN touch /usr/local/config.json


CMD ["djangur.py"]

ENTRYPOINT ["python3"]

# For some other command
# CMD ["python3", "djangur.py"]
