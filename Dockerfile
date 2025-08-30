FROM python:3.11-slim
WORKDIR /app
COPY app.py /app
RUN pip install flask psycopg2-binary gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]

