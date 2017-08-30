from server import Server

import sys
import yaml


def parse_settings(source='server.yml'):
    with open(source, 'r') as source_file:
        return yaml.load(source_file)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        settings = parse_settings(sys.argv[1])

    else:
        settings = parse_settings()

    server = Server(validators=settings.get('validators'), **settings.get('server', dict()))
    server.run()

