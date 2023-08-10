FROM alpine

RUN adduser nessus --disabled-password

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

RUN rm -rf /etc/localtime

RUN ln -s /usr/share/zoneinfo/Europe/Zagreb /etc/localtime

WORKDIR .

COPY ./generate_reports.py .

COPY ./requirements.txt .

RUN pip install -r requirements.txt --break-system-packages

USER nessus

ENTRYPOINT python3 generate_reports.py

