import docker

from actions import action, Action
from util import ConfigurationException


@action('docker')
class DockerAction(Action):
    client = docker.DockerClient()

    def __init__(self, **apis):
        if len(apis) != 1:
            raise ConfigurationException('The "docker" action has to have one API')

        api = next(key for key in apis)

        if len(apis[api]) != 1:
            raise ConfigurationException('The "docker" action has to have one command for the API')

        prop = next(key for key in apis[api])

        self.command = getattr(getattr(self.client, api), prop)

        self.arguments = apis[api][prop]
        if self.arguments is None:
            self.arguments = dict()

    def _run(self):
        print 'The whale says:', self.command(**self.arguments)

