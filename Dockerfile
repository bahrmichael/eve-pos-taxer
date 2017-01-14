FROM python:2.7-slim

RUN pip install pymongo eveapimongo

WORKDIR /home

COPY app.py /home

EXPOSE 9000

ENTRYPOINT ["python", "app.py"]