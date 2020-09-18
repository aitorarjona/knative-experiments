import os
import zmq
import time
import threading
import requests
import uuid
import subprocess
import logging
from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig()
logger = logging.getLogger('cloudbutton')
logger.setLevel(logging.DEBUG)

node = None
pool = None
addr = None


def init_node(pool_name, node_name):
    global node, pool, addr

    logger.debug('Init node')

    # Get container IP address
    cmd = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
    output, error = cmd.communicate()
    if error is not None:
        logger.error(error)

    # Get peer node addresses
    addr = output.decode('utf-8').strip()
    logger.debug('Node address: {}'.format(addr))
    url = '/'.join([os.environ['RENDEZVOUS_ENDPOINT'], 'pool', pool_name])
    logger.debug('Get pool from: {}'.format(url))
    res = requests.get(url, params={'node': node_name, 'address': addr})

    logger.debug('{}: {}'.format(res.status_code, res.text))
    if res.status_code != 200:
        raise Exception(res.text)

    res_json = res.json()
    pool = res_json['pool']

    # Start ping-pong server thread
    def server():
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        port = os.environ.get('ZMQ_PORT', 5555)
        logger.debug('Starting socket on port {}'.format(port))
        socket.bind('tcp://*:{}'.format(port))

        while True:
            logger.debug('Waiting for connection...')
            message = socket.recv()
            print(message)
            time.sleep(1)
            response = 'pong (i\'m node {} with address {})'.format(node, addr)
            socket.send(bytes(response, 'utf-8'))

    server_thread = threading.Thread(target=server)
    server_thread.start()
    node = node_name


@app.route('/work')
def work():
    global node
    pool_name = request.args.get('pool', default=None)
    node_name = request.args.get('node', default=None)
    if None in (pool_name, node_name):
        return jsonify({'error': '"pool" and "node" required'}), 400
    
    if node is None:
        try:
            init_node(pool_name, node_name)
        except Exception as e:
            return jsonify(str(e)), 400

    context = zmq.Context()
    port = os.environ.get('ZMQ_PORT', 5555)

    messages = []
    for inode, iaddr in pool.items():
        logging.debug('Connecting to node {} ({})'.format(inode, iaddr))
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://{}:{}'.format(iaddr, port))
        socket.send(b"ping")
        response = socket.recv()
        logging.debug('Received response {}'.format(response))
        messages.append(response.decode('utf-8'))

    return jsonify({'node': node, 'address': addr, 'pool': pool, 'result': messages})

@app.route('/', methods=['GET'])
def default():
    logging.debug('Hi')
    return 'Hi\n'


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
