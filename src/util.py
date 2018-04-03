import os
import sys
import time
import random

import six


class ConfigurationException(Exception):
    pass


class ActionInvocationException(Exception):
    pass


class ReplayRequested(Exception):
    def __init__(self, at):
        super(ReplayRequested, self).__init__()
        self.at = at


def import_action_module(file_path):
    directory = os.environ.get('TMP_IMPORT_DIR', '/tmp')

    module_name = 'action_%s_%s' % (int(1000.0 * time.time()), random.randint(1000, 9999))
    filename = '%s.py' % module_name

    tmp_file_path = os.path.join(directory, filename)

    try:
        with open(tmp_file_path, 'w') as tmp_file:
            with open(file_path, 'r') as input_file:
                tmp_file.write(input_file.read())

        sys_path = list(sys.path)
        sys.path.insert(0, directory)

        try:
            if six.PY34:
                import importlib.machinery
                loader = importlib.machinery.SourceFileLoader(module_name, tmp_file_path)
                loader.load_module()

            elif six.PY3:
                import importlib

                spec = importlib.util.spec_from_file_location(module_name, tmp_file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            else:
                __import__(module_name)

        finally:
            sys.path[:] = sys_path

    except Exception as ex:
        raise ConfigurationException(
            'Failed to import %s\nReason: (%s) %s' % (
                file_path, type(ex).__name__, ex
            )
        )

    finally:
        os.remove(tmp_file_path)

        # remove .pyc
        tmp_file_path += 'c'

        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


class classproperty(property):
    def __init__(self, fget):
        super(classproperty, self).__init__(classmethod(fget))

    def __get__(self, instance, owner):
        return self.fget.__get__(None, owner)()
