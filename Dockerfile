# This file is a template, and might need editing before it works on your project.
FROM python:3.6

WORKDIR ~/djangur

# COPY requirements.txt ~/djangur
# RUN pip install --no-cache-dir -r requirements.txt

COPY . ~/djangur

# For some other command
# CMD ["python", "djangur.py"]
