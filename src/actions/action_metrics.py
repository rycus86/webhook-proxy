from actions import action, Action


@action('metrics')
class MetricsAction(Action):
    def __init__(self, output=None, **kwargs):
        from server import Server

        self.app = Server.app

        for metric_type, configuration in kwargs.items():
            handler = getattr(self, metric_type)
            handler(**configuration)

    def counter(self, name, help=None, labels=None):
        pass

    def _run(self):
        pass

