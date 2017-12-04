import sys
import signal

import yaml

from server import Server


def parse_settings(source='server.yml'):
    with open(source, 'r') as source_file:
        return yaml.load(source_file)


def handle_signal(num, _):
    if num == signal.SIGTERM:
        exit(0)

    else:
        exit(1)


if __name__ == '__main__':
    settings = parse_settings(sys.argv[1]) if len(sys.argv) == 2 else parse_settings()
    
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    server = Server(endpoint_configurations=settings.get('endpoints'), **settings.get('server', dict()))
    server.run()
