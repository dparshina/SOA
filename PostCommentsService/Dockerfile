FROM python:3.10

WORKDIR /SOA

RUN pip install --no-cache-dir sqlalchemy pydantic_settings psycopg2
RUN pip install grpcio grpcio-tools

COPY . .

EXPOSE 50051

CMD ["python", "main.py"]