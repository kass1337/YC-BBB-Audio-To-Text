FROM ubuntu:focal-20240410 AS bot

RUN apt-get update
RUN apt-get install -y python3 python3-pip python-dev build-essential python3-venv
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get install -y --no-install-recommends ffmpeg

RUN mkdir -p /code
RUN mkdir -p ~/.aws

ADD . /code
WORKDIR /code

RUN find /code -type f -exec chmod 777 {} \;

RUN mv config ~/.aws
RUN mv credentials ~/.aws

RUN python3 -m pip install -r requirements.txt

ENTRYPOINT [ "python3", "/code/bot.py" ]