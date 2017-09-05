from __future__ import print_function

import os
import time
import traceback

from flask import request
from jinja2 import Template

from util import ActionInvocationException


def _safe_import():
    class SafeImportContext(object):
        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is ImportError:
                error_file = traceback.extract_tb(exc_tb)[1][0]
                name, _ = os.path.splitext(os.path.basename(error_file))
                
                if name.startswith('action_'):
                    name = name[len('action_'):]

                print('The "%s" action is not available' % name)

                return True

    return SafeImportContext()


def _register_available_actions():
    from action_log import LogAction
    from action_execute import ExecuteAction

    with _safe_import():
        from action_http import HttpAction
    with _safe_import():
        from action_docker import DockerAction


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

    def _render_with_template(self, template, **kwargs):
        template = Template(template)
        return template.render(request=request, timestamp=time.time(), datetime=time.ctime(), **kwargs)

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

