# This file is a template, and might need editing before it works on your project.
FROM python:3.6

WORKDIR /usr/local/djangur

# COPY requirements.txt ~/djangur
# RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/local/djangur
# COPY /usr/local/config.json /usr/local/djangur
# CMD ["pwd"]
# CMD ["ls"]

CMD cp /usr/local/config.json /usr/local/djangur/config.json
CMD ["djangur.py"]

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]

# For some other command
# CMD ["python3", "djangur.py"]
