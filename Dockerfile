FROM python:2.7-slim

RUN pip install json-logging-py pymongo

COPY classes/__init__.py /classes/__init__.py
COPY app.py /
COPY classes/mongoFactory.py /classes/mongoFactory.py
COPY classes/mongoProvider.py /classes/mongoProvider.py

EXPOSE 9000

ENTRYPOINT ["python", "app.py"]