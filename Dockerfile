# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm
WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
ENV FLASK_DEBUG=1
ENV FLASK_ENVIRONMENT=development
ENV FLASK_APP=app
CMD ["flask", "run", "--host=0.0.0.0"]
