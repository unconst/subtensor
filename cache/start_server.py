from opentensor import opentensor_pb2_grpc as opentensor_grpc
from server import Proxy

import argparse
import grpc
import socketserver
import threading
import time

from http.server import HTTPServer
from http.server import HTTPServer, CGIHTTPRequestHandler

from concurrent import futures
from datetime import timedelta
from loguru import logger
from timeloop import Timeloop

def set_timed_loops(tl, config, server):

    @tl.job(interval=timedelta(seconds=config.wait_refresh))
    def refresh():
        server.refresh()


def main(config):
    address = "[::]:" + str(config.port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    proxy_server = Proxy()
    opentensor_grpc.add_MetagraphProxyServicer_to_server(proxy_server, server)
    server.add_insecure_port(address)
    
    tl = Timeloop()
    set_timed_loops(tl, config, proxy_server)
    tl.start(block=False)
    logger.info('started timers')
 
    host_name = "localhost"
    httpd = HTTPServer((host_name, config.port+1), CGIHTTPRequestHandler)
    def http_thread_run():
        httpd.serve_forever()
    http_thread = threading.Thread(name='daemon', target=http_thread_run)
    http_thread.setDaemon(True)
    http_thread.start()
    
    server.start()
    logger.info('metagraph server {} ...', address)
    server.wait_for_termination()

    del http_server

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--wait_refresh',
        default=10,
        type=int,
        help="Time between stale entry cleaning. Default=20")
    parser.add_argument(
        '--port',
        default=8899,
        type=int,
        help="Port to serve on. Default=12931")
    parser.add_argument(
        '--time_to_live',
        default=20,
        type=int,
        help="Time that stale entries remain in metagraph. Default=20")
    params = parser.parse_args()
    main(params)

