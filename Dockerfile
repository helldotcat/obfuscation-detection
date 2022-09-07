FROM ubuntu:bionic

RUN apt-get update && apt-get install nodejs npm python3 python3-pip git -y
# RUN python3 -m pip install -U --force-reinstall pip
RUN pip3 install -U pip
RUN pip3 install --upgrade setuptools

RUN pip3 install aiohttp catboost
RUN npm i -g acorn

COPY ./service /app
COPY ./converter /app/converter

CMD ["python3", "/app/main.py"]
