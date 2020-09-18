FROM python:3.8.2-slim-buster

ENV PYTHONUNBUFFERED True
ENV PORT 8080

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./app ./

#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
CMD python app.py