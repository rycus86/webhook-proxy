import sys

import yaml

from server import Server


def parse_settings(source='server.yml'):
    with open(source, 'r') as source_file:
        return yaml.load(source_file)


if __name__ == '__main__':
    settings = parse_settings(sys.argv[1]) if len(sys.argv) == 2 else parse_settings()

    server = Server(endpoint_configurations=settings.get('endpoints'), **settings.get('server', dict()))
    server.run()
