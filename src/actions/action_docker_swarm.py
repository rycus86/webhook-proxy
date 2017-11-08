from __future__ import print_function

from docker.utils import version_lt as docker_version_less_than

from actions import action
from actions.action_docker import DockerAction


@action('docker-swarm')
class DockerSwarmAction(DockerAction):
    def __init__(self, output='{{ result }}', **invocations):
        super(DockerSwarmAction, self).__init__(output, **invocations)

    def _target(self):
        return self

    def restart(self, service_id):
        service = self.client.services.get(self._render_with_template(service_id))

        return self._update_service(service, force_update=True)

    def scale(self):
        pass

    def update(self):
        pass

    def _update_service(self, service, **kwargs):
        raw = service.attrs
        spec = raw['Spec']

        service_id = raw['ID']
        version = raw['Version']['Index']
        task_template = spec['TaskTemplate']
        name = spec['Name']
        labels = spec.get('Labels')
        mode = spec['Mode']
        update_config = spec.get('UpdateConfig')
        networks = task_template.get('Networks') or spec.get('Networks')
        endpoint_spec = spec.get('EndpointSpec')

        if kwargs.get('force_update', False):
            if docker_version_less_than(self.client.api.api_version, '1.25'):
                raise PyGenException('Force updating a service is not available on API version %s (< 1.25)' %
                                     self.client.api.api_version)

            task_template['ForceUpdate'] = (task_template['ForceUpdate'] + 1) % 100

        # fix SDK bug on 17.06 -- https://github.com/moby/moby/issues/34116
        task_template['container_spec'] = task_template.get('ContainerSpec')

        return self.client.api.update_service(service=service_id,
                                              version=version,
                                              task_template=task_template,
                                              name=name,
                                              labels=labels,
                                              mode=mode,
                                              update_config=update_config,
                                              networks=networks,
                                              endpoint_spec=endpoint_spec)

