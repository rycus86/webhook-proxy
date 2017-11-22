from unittest_helper import ActionTestBase
from actions.action_docker_swarm import DockerSwarmAction


class DockerSwarmActionTest(ActionTestBase):
    def setUp(self):
        self.mock_client = MockClient()
        DockerSwarmAction.client = self.mock_client

    def test_restart(self):
        self._invoke({'docker-swarm': {'$restart': {'service_id': 'mock-service'}}})

        self.verify('name', 'mock-service')
        self.verify('task_template.ForceUpdate', 1)

        self.mock_client.service_attributes = {
            'Spec': {'TaskTemplate': {'ForceUpdate': 12}}
        }

        self._invoke({'docker-swarm': {'$restart': {'service_id': 'fake'}}})

        self.verify('task_template.ForceUpdate', 13)

    def test_scale(self):
        self._invoke({'docker-swarm': {'$scale': {'service_id': 'mocked', 'replicas': 12}}})

        self.verify('mode.Replicated.Replicas', 12)

    def test_update(self):
        self._invoke({'docker-swarm': {'$update': {
            'service_id': 'updating', 
            'image': 'test-image:1.0.y'
        }}})
        
        self.verify('task_template.ContainerSpec.Image', 'test-image:1.0.y')

        self._invoke({'docker-swarm': {'$update': {
            'service_id': 'updating', 
            'container_labels': [{'test.label': 'test', 'mock.label': 'mock'}]
        }}})
        
        self.verify('task_template.ContainerSpec.Labels',
                    [{'test.label': 'test', 'mock.label': 'mock'}])

        self._invoke({'docker-swarm': {'$update': {
            'service_id': 'updating', 
            'labels': [{'service.label': 'testing'}]
        }}})
        
        self.verify('labels', [{'service.label': 'testing'}])

        self._invoke({'docker-swarm': {'$update': {
            'service_id': 'updating', 
            'resources': {'mem_limit': 512}
        }}})
        
        self.verify('task_template.Resources.Limits.MemoryBytes', 512)

    def verify(self, key, value):
        def assertPropertyEquals(data, prop):
            self.assertIsNotNone(data)

            if '.' in prop:
                current, remainder = prop.split('.', 1)
                assertPropertyEquals(data.get(current), remainder)
            else:
                self.assertEqual(data.get(prop), value,
                                 msg='%s != %s for %s' % (data.get(prop), value, key))

        assertPropertyEquals(self.mock_client.last_update, key)


class MockClient(object):
    def __init__(self):
        self.last_update = dict()
        self.service_attributes = None

    @property
    def api(self):
        return Mock(api_version='1.30', update_service=self.update_service)

    @property
    def services(self):
        return self

    def get(self, *args, **kwargs):
        details = Mock(attrs={
            'ID': 'testId',
            'Version': {'Index': 12},
            'Spec': {
                'Name': args[0],
                'Mode': {'Replicated': {'Replicas': 1}},
                'TaskTemplate': {
                    'ContainerSpec': {
                        'Image': 'alpine:mock'
                    },
                    'ForceUpdate': 0
                }
            }
        }, 
        reload=lambda: True,
        decode=lambda: details)
        
        if self.service_attributes:
            self._merge_attributes(details.attrs, self.service_attributes)

        return details

    def _merge_attributes(self, details, overwrite):
        for key, value in overwrite.items():
            if key not in details:
                details[key] = value
            elif isinstance(value, dict):
                self._merge_attributes(details[key], overwrite[key])
            else:
                details[key] = value

    def update_service(self, **kwargs):
        self.last_update = kwargs
        return True


class Mock(dict):
    def __getattr__(self, name):
        return self.get(name)

