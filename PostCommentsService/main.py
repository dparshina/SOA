import grpc
import time
from concurrent import futures
import post_service_pb2
import post_service_pb2_grpc
from grpc_api import postService


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_service_pb2_grpc.add_postServiceServicer_to_server(postService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC Post Service запущен на порту 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    main()