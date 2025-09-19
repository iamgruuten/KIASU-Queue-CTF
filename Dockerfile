FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask psycopg2-binary pyjwt
EXPOSE 5000
ENV FLASK_APP=flask_app.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
