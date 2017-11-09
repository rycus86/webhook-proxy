from __future__ import print_function

from docker.types.services import ContainerSpec, SecretReference
from docker.types.services import TaskTemplate, Resources, RestartPolicy, Placement
from docker.types.services import UpdateConfig, EndpointSpec
from docker.utils import version_lt as docker_version_less_than

from actions import action, ActionInvocationException
from actions.action_docker import DockerAction


@action('docker-swarm')
class DockerSwarmAction(DockerAction):
    def __init__(self, output='{{ result }}', **invocations):
        super(DockerSwarmAction, self).__init__(output, **invocations)

    def _target(self):
        return self

    def restart(self, service_id):
        return self._update_service(service_id, force_update=True)

    def scale(self, service_id, replicas):
        return self._update_service(service_id, replicas=replicas)

    def update(self, service_id, **kwargs):
        return self._update_service(service_id, **self._process_arguments(kwargs))

    def _update_service(self, service_id, **kwargs):
        service = self.client.services.get(self._render_with_template(service_id))

        if self._execute_update(service, **kwargs):
            service.reload()

            return service

    def _execute_update(self, service, **kwargs):
        raw = service.attrs
        spec = raw['Spec']

        service_id = raw['ID']
        version = raw['Version']['Index']
        task_template = spec['TaskTemplate']
        container_spec = task_template['ContainerSpec']
        name = spec['Name']
        labels = spec.get('Labels')
        mode = spec['Mode']
        update_config = spec.get('UpdateConfig')
        networks = task_template.get('Networks') or spec.get('Networks')
        endpoint_spec = spec.get('EndpointSpec')

        container_spec.update(**self._get_container_spec(container_spec, **kwargs))
        task_template.update(**self._get_task_template(task_template, container_spec, **kwargs))

        if 'labels' in kwargs:
            labels = kwargs['labels']

        if 'replicas' in kwargs:
            mode['Replicated']['Replicas'] = int(kwargs['replicas'])

        if 'update_config' in kwargs:
            update_config = UpdateConfig(**kwargs['update_config'])

        if 'networks' in kwargs:
            networks = kwargs['networks']

        if 'endpoint_spec' in kwargs:
            endpoint_spec = EndpointSpec(**kwargs['endpoint_spec'])

        return self.client.api.update_service(service=service_id,
                                              version=version,
                                              task_template=task_template,
                                              name=name,
                                              labels=labels,
                                              mode=mode,
                                              update_config=update_config,
                                              networks=networks,
                                              endpoint_spec=endpoint_spec)

    @staticmethod
    def _get_container_spec(container_spec, **kwargs):
        container_spec_keys = ('image', 'command', 'args', 'hostname', 'env', 'dir',
                               'user', 'mounts', 'stop_grace_period', 'tty')

        container_spec_args = dict()

        if 'container_labels' in kwargs:
            container_spec_args['labels'] = kwargs['container_labels']

        for key in container_spec_keys:
            if key in kwargs:
                container_spec_args[key] = kwargs[key]

        if 'secrets' in kwargs:
            container_spec_args['secrets'] = list(SecretReference(item) for item in kwargs['secrets'])

        container_spec_defaults = dict(image='Image', command='Command', args='Args')

        for arg, key in container_spec_defaults.items():
            if arg not in container_spec_args:
                container_spec_args[arg] = container_spec.get(key)

        return ContainerSpec(**container_spec_args)

    def _get_task_template(self, task_template, container_spec, **kwargs):
        task_template_keys = dict(resources=Resources, restart_policy=RestartPolicy, placement=Placement)
        task_template_args = dict()

        task_template_args['container_spec'] = container_spec

        for key, value_type in task_template_keys.items():
            if key in kwargs:
                task_template_args[key] = task_template_keys[key](kwargs[key])

        if kwargs.get('force_update', False):
            if docker_version_less_than(self.client.api.api_version, '1.25'):
                raise ActionInvocationException('Force updating a service is not available on API version %s (< 1.25)' %
                                                self.client.api.api_version)

            task_template_args['force_update'] = (task_template['ForceUpdate'] + 1) % 100

        return TaskTemplate(**task_template_args)
