FROM python:2.7-slim

RUN pip install pymongo

WORKDIR /home

COPY classes /home/classes
COPY app.py /home

EXPOSE 9000

ENTRYPOINT ["python", "app.py"]