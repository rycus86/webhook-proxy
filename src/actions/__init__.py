from util import ActionInvocationException

def _register_available_actions():
    from log import LogAction
    from http import HttpAction


class Action(object):
    _registered_actions = dict()
    
    def run(self):
        try:
            return self._run()

        except Exception as ex:
            raise ActionInvocationException('Failed to invoke %s.run: %s' %
                                            (type(self).__name__, ex), ex)

    def _run(self):
        raise ActionInvocationException('%s.run not implemented' % type(self).__name__)

    @classmethod
    def register(cls, name, action_type):
        cls._registered_actions[name] = action_type

    @classmethod
    def create(cls, name, **settings):
        if name not in cls._registered_actions:
            raise ActionInvocationException('Unkown action: %s (registered: %s)' %
                                            (name, cls._registered_actions.keys()))
        
        return cls._registered_actions[name](**settings)


def action(name):
    def invoke(cls):
        Action.register(name, cls)

    return invoke


_register_available_actions()

