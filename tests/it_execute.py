from integrationtest_helper import IntegrationTestBase


class ExecuteIntegrationTest(IntegrationTestBase):
    
    def test_a(self):
        t = """
        server:
          port: 9001

        endpoints:
          - /test:
              method: 'POST'

              actions:
                - log:
        """
        
        self.prepare_file('sample.yml', t)

        container = self.remote_client.containers.run('webhook-testing',
                                                      name='wht-01',
                                                      command='/tmp/sample.yml',
                                                      ports={'9001': '9001'},
                                                      volumes=['/tmp:/tmp:ro'],
                                                      detach=True)

        """ WIP        
        import time
        time.sleep(2)

        print 'logs:', container.logs()

        print self.dind_container.exec_run(['ls', '-l', '/tmp'])
        print self.dind_container.exec_run(['cat', '/tmp/sample.yml'])
        """

