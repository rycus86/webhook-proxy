from integrationtest_helper import IntegrationTestBase


class MetricsIntegrationTest(IntegrationTestBase):

    def test_metrics(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /test/metrics:
              method: 'POST'

              actions:
                - log:
                - log:
                    message: Plain text
                - log:
                    message: 'With request data: {{ request.json.content }}'
        """

        self.prepare_file('test-51.yml', config)

        self.start_app_container('test-51.yml')

        response = self.request('/test/metrics', content='sample')

        self.assertEqual(response.status_code, 200)

        response = self.metrics()

        self.assertEqual(response.status_code, 200)
        
        metrics = response.text

        self.assertIn('python_info{', metrics)
        self.assertIn('process_start_time_seconds ', metrics)

        self.assertIn('flask_http_request_total{'
                      'method="POST",status="200"} 1.0', metrics)
        self.assertIn('flask_http_request_duration_seconds_count{'
                      'method="POST",path="/test/metrics",status="200"} 1.0', metrics)

        self.assertIn('webhook_proxy_actions_count{'
                      'action_index="0",action_type="log",'
                      'http_method="POST",http_route="/test/metrics"} 1.0', metrics)
        self.assertIn('webhook_proxy_actions_count{'
                      'action_index="1",action_type="log",'
                      'http_method="POST",http_route="/test/metrics"} 1.0', metrics)
        self.assertIn('webhook_proxy_actions_count{'
                      'action_index="2",action_type="log",'
                      'http_method="POST",http_route="/test/metrics"} 1.0', metrics)
