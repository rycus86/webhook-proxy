from __future__ import print_function

from actions import action
from actions.action_docker import DockerAction


@action('docker-swarm')
class DockerSwarmAction(DockerAction):
    def __init__(self, output='{{ result }}', **invocations):
        super(DockerSwarmAction, self).__init__(output, **invocations)
        print(
            'The `docker-swarm` is now deprecated, use the `docker` action '
            'with `$services.$get` and `service.update(..)`'
        )

    def _target(self):
        return self

    def restart(self, service_id):
        print(
            'Instead of `docker-swarm.$restart` please use `docker.$services.$get(id)` '
            'and `service.update(force_update=num)`'
        )
        return self._update_service(service_id, force_update=True)

    def scale(self, service_id, replicas):
        print(
            'Instead of `docker-swarm.$scale` please use `docker.$services.$get(id)` '
            'and `service.update(mode={"replicated": {"Replicas": num}})`'
        )
        return self._update_service(service_id, mode={'replicated': {'Replicas': int(replicas)}})

    def update(self, service_id, **kwargs):
        print(
            'Instead of `docker-swarm.$update` please use `docker.$services.$get(id)` '
            'and `service.update(**kwargs)`'
        )
        return self._update_service(service_id, **kwargs)

    def _update_service(self, service_id, **kwargs):
        service = self.client.services.get(self._render_with_template(service_id))

        if 'force_update' in kwargs and isinstance(kwargs['force_update'], bool):
            current = service.attrs['Spec']['TaskTemplate'].get('ForceUpdate', 0)
            kwargs['force_update'] = (current + 1) % 100

        if service.update(**self._process_arguments(kwargs)):
            service.reload()

            return service
