FROM python:3.12-slim

WORKDIR /app

COPY . .


RUN pip install --no-cache-dir flask
ENV PYTHONPATH=/app
EXPOSE 5001

CMD ["python", "visual/app.py"]