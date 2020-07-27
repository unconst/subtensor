from opentensor import opentensor_pb2_grpc as opentensor_grpc
from metagraph import Metagraph

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

GOSSIP_STEP = 10
CLEAN_STEP = 10
TTL = 60*60

def set_timed_loops(tl, config, server):

    @tl.job(interval=timedelta(seconds=GOSSIP_STEP))
    def gossip():
        server.do_gossip()

    @tl.job(interval=timedelta(seconds=CLEAN_STEP))
    def gossip():
        server.do_clean(TTL)

def main(config):
    
    # Build backend server.
    address = "[::]:" + str(config.port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    metagraph = Metagraph()
    opentensor_grpc.add_MetagraphServicer_to_server(metagraph, server)
    server.add_insecure_port(address)
    
    # Start timers.
    tl = Timeloop()
    set_timed_loops(tl, config, metagraph)
    tl.start(block=False)
    logger.info('started timers ...')
 
    # Build frontend.
    host_name = "localhost"
    httpd = HTTPServer((host_name, config.port+1), CGIHTTPRequestHandler)
    def http_thread_run():
        httpd.serve_forever()
    http_thread = threading.Thread(name='daemon', target=http_thread_run)
    http_thread.setDaemon(True)
    http_thread.start()
    
    # Start metagraph.
    server.start()
    logger.info('metagraph server {} ...', address)
    server.wait_for_termination()

    del http_server

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port',
        default=8899,
        type=int,
        help="Port to serve on. Default=12931")
    params = parser.parse_args()
    main(params)

