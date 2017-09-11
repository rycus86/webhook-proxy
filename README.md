# Webhook Proxy

A simple `Python` [Flask](http://flask.pocoo.org) *REST* server to
accept *JSON* webhooks and run actions as a result.

[![Build Status](https://travis-ci.org/rycus86/webhook-proxy.svg?branch=master)](https://travis-ci.org/rycus86/webhook-proxy)
[![Build Status](https://img.shields.io/docker/build/rycus86/webhook-proxy.svg)](https://hub.docker.com/r/rycus86/webhook-proxy)
[![Coverage Status](https://coveralls.io/repos/github/rycus86/webhook-proxy/badge.svg?branch=master)](https://coveralls.io/github/rycus86/webhook-proxy?branch=master)
[![Code Climate](https://codeclimate.com/github/rycus86/webhook-proxy/badges/gpa.svg)](https://codeclimate.com/github/rycus86/webhook-proxy)

## Usage

    TODO

## Configuration

The configuration for the server and its endpoints is described in a *YAML* file.

A short example:

```yaml
server:
  host: '127.0.0.1'
  port: '5000'

endpoints:
  - /endpoint/path
      method: 'POST'

      headers:
        X-Sender: 'regex for X-Sender HTTP header'

      body:
        project:
          name: 'regex for project.name in the JSON payload'
          items:
            name: '^example_[0-9]+'
      
      actions:
        - log:
            message: 'Processing {{ request.path }} ...'
```

### server

The `server` section defines settings for the HTTP server receiving the webhook requests.

| key | description | default | required |
| --- | ----------- | ------- | -------- |
| host | The host name or address for the server to listen on | `127.0.0.1` | no |
| port | The port number to accept incoming connections on    | `5000`      | no |

### endpoints

The `endpoints` section configures the list of endpoints exposed on the server.

Each endpoint supports the following configuration (all optional):

| key | description | default |
| --- | ----------- | ------- |
| method   | HTTP method supported on the endpoint           | `POST`  |
| headers  | HTTP header validation rules as a dictionary of names to regular expressions  | `empty` |
| body     | Validation rules for the JSON payload in the request body.<br/>Supports lists too, the `project.item.name` in the example the payload `{"project": {"name": "...", "items": [{"name": "example_12"}]}}` would be accepted as an incoming body.    | `empty` |
| actions  | List of actions to execute for valid requests.  | `empty` |

### actions

Action definitions support variables for most properties using _Jinja2_ templates.
By default, these receive the following objects in their context:

- `request`   : the incoming _Flask_ request being handled
- `timestamp` : the Epoch timestamp as `time.time()`
- `datetime`  : human-readable timestamp as `time.ctime()`

The following actions are supported (given their dependencies are met).

#### log

The `log` action prints a message on the standard output. 

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| message | The log message template | `Processing {{ request.path }} ...` | yes | no |

#### execute

The `execute` action executes an external command using `subprocess.check_output`.
The output (string) of the invocation is passed to the _Jinja2_ template as `result`.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| command | The command to execute as a string or list | | no | yes |
| shell   | Configuration for the shell used.<br/>Accepts a boolean (whether to use the default shell or run the command directly) or a string (the shell command that supports `-c`) or a list (for the complete shell prefix, like `['bash', '-c']`)   | `True` | no | no |
| output  | Output template for printing the result on the standard output | `{{ result }}` | yes | no |

#### http

The `http` action sends an HTTP request to a target and requires the __requests__ Python module.
The HTTP response object (from the _requests_ module) is available to the
_Jinja2_ template as `response`.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| target  | The target endpoint as `<scheme>://<host>[:<port>][/<path>]` | | no | yes |
| method  | The HTTP method to use for the request                  | `POST`  | no  | no |
| headers | The HTTP headers (as dictionary) to add to the request  | `empty` | yes | no |
| body    | The HTTP body (as string) to send with the request      | `empty` | yes | no |
| output  | Output template for printing the response on the standard output | `HTTP {{ response.status_code }} : {{ response.content }}` | yes | no |

#### docker

The `docker` action interacts with the _Docker_ daemon and requires the __docker__ Python module.
It also needs access to the _Docker_ UNIX socket at `/var/run/docker.sock`.

The action supports _exactly one_ invocation on the _Docker_ client (per action).
Invocations (or properties) are keys starting with `$` in the configuration,
for example listing the containers would use `$containers` with `$list` as a sub-item.
The result of the invocation (as an object from the _Docker_ client) is available to the
_Jinja2_ templates as `result`.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| `$invocation` | Exactly one invocation supported by the _Docker_ client (see examples below) | | yes (for values) | yes |
| output | Output template for printing the result on the standard output | `{{ result }}` | yes | no |

Examples:

```yaml
...
  actions:
    - docker:
        $containers:
          $list:
            filters:
              name: '{{ request.json.repo.name }}'
        output: |
          Containers matching "{{ request.json.name }}":
          {% for container in result %}
           - {{ container.name }} @ {{ container.short_id }}
          {% endfor %}

    - docker:
        $info:
        output: 'Docker version: {{ result.ServerVersion }} on {{ result.OperatingSystem }}'

    - docker:
        $images:
          $pull:
            repository: '{{ request.json.namespace }}/{{ request.json.name }}'
            tag: '{{ request.json.get('tag', 'latest') }}'

    - docker:
        $run:
          image: 'alpine'
          command: 'echo "Hello {{ request.json.message }}!"'
          remove: true
```

#### docker-compose

The `docker-compose` action interacts with _Docker Compose_ and requires the `docker-compose` Python module.

The action supports _exactly one_ invocation on the _Docker Compose_ project (per action).
The invocations are in the same format as with the `docker` action and the
result is available for _Jinja2_ templates as `result` that is the return object
from the _Docker Compose_ invocation.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| project\_name | The _Compose_ project name | | no | yes |
| directory     | The directory of the _Compose_ project | | no | yes |
| composefile   | The filename of the _Composefile_ within the directory | `docker-compose.yml` | no | no |
| `$invocation` | Exactly one invocation supported by the _Docker Compose_ client (see examples below) | | yes (for values) | yes |
| output | Output template for printing the result on the standard output | `{{ result }}` | yes | no |

Examples:

```yaml
...
  actions:
    - docker-compose:
        project_name: 'web'
        directory: '/opt/projects/web'
        $get_services:
        output: |
          Compose services:
          {% for service in result %}
           - service: {{ service.name }}
          {% endfor %}

    - docker-compose:
        project_name: 'backend'
        directory: '/opt/projects/compose_project'
        $up:
          detached: true
        output: |
          Containers started:
          {% for container in result %}
           - {{ container.name }}
          {% endfor %}

    - docker-compose:
        project_name: 'backend'
        directory: '/opt/projects/compose_project'
        $down:
          remove_image_type: false
          include_volumes: true
        output: 'Compose project stopped'
```

## Docker

    TODO

