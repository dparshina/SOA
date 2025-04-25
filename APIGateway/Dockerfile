FROM python:3.10

WORKDIR /SOA

RUN pip install --no-cache-dir fastapi requests uvicorn pydantic pydantic_settings
RUN pip install grpcio grpcio-tools

COPY . .
CMD ["uvicorn", "proxy_service:api", "--host", "0.0.0.0", "--port", "8000", "--reload"]