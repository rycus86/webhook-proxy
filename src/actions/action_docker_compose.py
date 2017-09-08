from __future__ import print_function

from compose.config.config import ConfigFile, ConfigDetails
from compose.config.config import load as load_config
from compose.project import Project

from actions import action
from actions.action_docker import DockerAction


@action('docker-compose')
class DockerComposeAction(DockerAction):
    def __init__(self, project_name, directory, composefile='docker-compose.yml', output='{{ result }}', **invocations):
        config = ConfigFile.from_filename('%s/%s' % (directory, composefile))
        details = ConfigDetails(directory, [config])
        self.project = Project.from_config(project_name, load_config(details), self.client.api)

        super(DockerComposeAction, self).__init__(output, **invocations)

    def _target(self):
        return self.project
