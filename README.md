# Webhook Proxy

A simple `Python` [Flask](http://flask.pocoo.org) *REST* server to
accept *JSON* webhooks and run actions as a result.

[![Build Status](https://travis-ci.org/rycus86/webhook-proxy.svg?branch=master)](https://travis-ci.org/rycus86/webhook-proxy)
[![Build Status](https://img.shields.io/docker/build/rycus86/webhook-proxy.svg)](https://hub.docker.com/r/rycus86/webhook-proxy)
[![Coverage Status](https://coveralls.io/repos/github/rycus86/webhook-proxy/badge.svg?branch=master)](https://coveralls.io/github/rycus86/webhook-proxy?branch=master)
[![Code Climate](https://codeclimate.com/github/rycus86/webhook-proxy/badges/gpa.svg)](https://codeclimate.com/github/rycus86/webhook-proxy)

## Usage

To start the server, run:

```shell
python app.py [server.yml]
```

If the parameter is omitted, the configuration file is expected to be `server.yml`
in the current directory (see configuration details below).

The application can be run using Python 2 or 3.

## Configuration

The configuration for the server and its endpoints is described in a *YAML* file.

A short example:

```yaml
server:
  host: '127.0.0.1'
  port: '5000'

endpoints:
  - /endpoint/path:
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
| host | The host name or address for the server to listen on  | `127.0.0.1` | no |
| port | The port number to accept incoming connections on     | `5000`      | no |
| imports | Python modules (as list of file paths) to import for registering additional actions | `None` | no |

Set the `host` to `0.0.0.0` to accept connections from any hosts.

The `imports` property has to be a `list` and should point to the `.py` files.
They will be copied temporarily into the `TMP_IMPORT_DIR` folder (`/tmp` by default,
override with the environment variable) then renamed to a random filename and
finally imported as a module so that we can load multiple modules with the same
filename from different paths.
Also note that because of this, we cannot rely on the module `__name__`.

### endpoints

The `endpoints` section configures the list of endpoints exposed on the server.

Each endpoint supports the following configuration (all optional):

| key | description | default |
| --- | ----------- | ------- |
| method   | HTTP method supported on the endpoint           | `POST`  |
| headers  | HTTP header validation rules as a dictionary of names to regular expressions  | `empty` |
| body     | Validation rules for the JSON payload in the request body                     | `empty` |
| async    | Execute the action asynchronously               | `False` |
| actions  | List of actions to execute for valid requests.  | `empty` |

The message body validation supports lists too, the `project.item.name` in the example would accept
`{"project": {"name": "...", "items": [{"name": "example_12"}]}}` as an incoming body.

### actions

Action definitions support variables for most properties using _Jinja2_ templates.
By default, these receive the following objects in their context:

- `request`   : the incoming _Flask_ request being handled
- `timestamp` : the Epoch timestamp as `time.time()`
- `datetime`  : human-readable timestamp as `time.ctime()`
- `own_container_id`: the ID of the container the app is running in or otherwise `None`
- `read_config`: helper for reading configuration parameters from key-value files
  or environment variables and also full configuration files (certificates for example),
  see [docker_helper](https://github.com/rycus86/docker_helper) for more information and usage
- `error(..)` : a function with an optional `message` argument to raise errors when evaluating templates
- `context`   : a thread-local object for passing information from one action to another

_Jinja2_ does not let you execute code in the templates directly, so to use
the `error` and `context` objects you need to do something like this:

```
{% if 'something' is 'wrong' %}
  
  {# treat it as literal (will display None) #}
  {{ error('Something is not right }}

  {# or use the assignment block with a dummy variable #}
  {% set _ = error() %}

{% else %}

  {% set _ = context.set('verdict', 'All good') %}

{% endif %}

## In another action's template:

  Previously we said {{ context.verdict }}
```

The following actions are supported (given their dependencies are met).

#### log

The `log` action prints a message on the standard output. 

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| message | The log message template | `Processing {{ request.path }} ...` | yes | no |

#### eval

The `eval` action evaluates a _Jinja2_ template block.
This can be useful to work with objects passed through from previous actions using
the `context` for example.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| block | The template block to evaluate | | yes | yes |

#### execute

The `execute` action executes an external command using `subprocess.check_output`.
The output (string) of the invocation is passed to the _Jinja2_ template as `result`.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| command | The command to execute as a string or list                     |                | no  | yes |
| shell   | Configuration for the shell used (see below)                   | `True`         | no  | no  |
| output  | Output template for printing the result on the standard output | `{{ result }}` | yes | no  |

The `shell` parameter accepts:

- boolean : whether to use the default shell or run the command directly
- string  : a shell command that supports `-c`
- list    : for the complete shell prefix, like `['bash', '-c']`

#### http

The `http` action sends an HTTP request to a target and requires the __requests__ Python module.
The HTTP response object (from the _requests_ module) is available to the
_Jinja2_ template as `response`.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| target  | The target endpoint as `<scheme>://<host>[:<port>][/<path>]`                        |    | no  | yes |
| method  | The HTTP method to use for the request                                              | `POST`  | no  | no  |
| headers | The HTTP headers (as dictionary) to add to the request                              | `empty` | yes | no  |
| json    | whether to dump `body` YAML subtree as json                                         | `False` | no  | no  |
| body    | The HTTP body to send with the request. String (or YAML tree, if `json` is `True`)  | `empty` | yes | no  |
| output  | Output template for printing the response on the standard output                    | `HTTP {{ response.status_code }} : {{ response.content }}` | yes | no |

#### github-verify

The `github-verify` is a convenience action to validate incoming _GitHub_ webhooks.
It requires the webhook to be signed with a secret.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| secret | The webhook secret configured in _GitHub_ | | yes | yes |
| output  | Output template for printing a message on the standard output | `{{ result }}` | yes | no |

The action will raise an `ActionInvocationException` on failure.
If that happens, the actions defined after this one will not be executed.

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
| `$invocation` | Exactly one invocation supported by the _Docker_ client (see examples below) |                | yes (for values) | yes |
| output        | Output template for printing the result on the standard output               | `{{ result }}` | yes              | no  |

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
        $containers:
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
| project\_name | The _Compose_ project name             | | no | yes |
| directory     | The directory of the _Compose_ project | | no | yes |
| composefile   | The filename of the _Composefile_ within the directory          | `docker-compose.yml` | no  | no |
| `$invocation` | Exactly one invocation supported by the _Docker Compose_ client (see examples below) | | yes (for values) | yes |
| output | Output template for printing the result on the standard output         | `{{ result }}`       | yes | no |

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

#### docker-swarm (deprecated)

*Since the merge of [docker-py#1807](https://github.com/docker/docker-py/pull/1807),
this convenience action is no longer necessary.
The official Docker SDK can handle Swarm service updates nicely.*

The `docker-swarm` action exposes convenience _Docker_ actions for _Swarm_ related operations
that might require quite a bit of manual work to replicate with the `docker` action.

The action supports _exactly one_ invocation (per action) on its own action object.
The invocations are in the same format as with the `docker` action and the available
ones are:

- `$restart`: restarts (force updates) a _Swarm_ service matching the `service_id` parameter
  (this can be a service name or ID)
- `$scale`: updates a __replicated__ service matched by `service_id` to have `replicas` number
  of instances
- `$update`: updates a service matched by `service_id`

The update invocation uses the current service spec and updates them with the following
parameters if they are present:

- `image`, `command`, `args`, `hostname`, `env`, `dir`, `user`, `mounts`, `stop_grace_period`, `tty`
  for the container specification (see `docker.types.services.ContainerSpec`)
- `container_labels` for container labels
- `secrets` for secret references as a list of dictionaries
  (see `docker.types.services.SecretReference`) 
- `resources`, `restart_policy`, `placement` for the task template specification
  (see `docker.types.services.TaskTemplate`)
- `labels` for service labels
- `replicas` for number of instances for __replicated__ services
- `update_config` for the service update configuration
  (see `docker.types.services.UpdateConfig`)
- `networks` as a list of network IDs or names
- `endpoint_spec` for the endpoint specification
  (see `docker.types.services.EndpointSpec`)

The result of the invocations will be the service object if the service update was successful. 

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| `$invocation` | Exactly one invocation supported by the action (see examples below) | | yes (for values) | yes |
| output | Output template for printing the result on the standard output | `{{ result }}` | yes | no |

Examples:

```yaml
...
  actions:
    - docker-swarm:
        $restart:
          service_id: '{{ request.json.service }}'
        output: >
          Service restarted: {{ result.name }}

    - docker-swarm:
        $scale:
          service_id: '{{ request.json.service }}'
          replicas: '{{ request.json.replicas }}'

    - docker-swarm:
        $update:
          service_id: '{{ request.json.service }}'
          command: '{{ request.json.command }}'
          labels:
            label_1: 'sample'
            label_2: '{{ request.json.label }}'
```

#### sleep

The `sleep` action waits for a given time period.
It may be useful if an action has executed something asynchronous and another action
relies on the outcome that would only happen a little bit later.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| seconds | Number of seconds to sleep for | | yes | yes | 
| message | The message template to print on the standard output | `Waiting {{ seconds }} seconds before continuing ...` | yes | no |

#### metrics

The application exposes [Prometheus](https://prometheus.io/) metrics
about the number of calls and the execution times of the endpoints.

The `metrics` action registers a new metric in addition that
tracks the entire execution of the endpoint (not only the action).
Apart from the optional `output` configuration it has to contain
one metric registration from the table below.

| key | description | default | templated | required |
| --- | ----------- | ------- | --------- | -------- |
| histogram | Registers a Histogram | | yes (labels) | yes (one) | 
| summary   | Registers a Summary   | | yes (labels) | yes (one) |
| gauge     | Registers a Gauge     | | yes (labels) | yes (one) |
| counter   | Registers a Counter   | | yes (labels) | yes (one) |
| message | The message template to print on the standard output | `Waiting {{ seconds }} seconds before continuing ...` | yes | no |
| output | Output template for printing the result on the standard output         | `Tracking metrics: {{ metric }}`       | yes | no |

Note that the `name` configuration is mandatory for metrics.
Also note that metric labels are accepted as a dictionary where
the value can be templated and will be evaluated within
the Flask request context.
The templates also have access to the Flask `response` object
(with the `gauge` being the exception as it is also evaluated
before the request to track in-progress executions).

For example:

```yaml
...
  actions:
    - metrics:
        gauge:
          name: requests_in_progress
          help: Tracks current requests in progress
          
    - metrics:
        summary:
          name: request_summary
          labels:
            path: '{{ request.path }}'
...
```

## Docker

The application can be run in *Docker* containers using images based on *Alpine Linux*
for 3 processor architectures with the following tags:

- `latest`: for *x86* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy.svg)](https://microbadger.com/images/rycus86/webhook-proxy "Get your own image badge on microbadger.com")
- `armhf`: for *32-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy:armhf.svg)](https://microbadger.com/images/rycus86/webhook-proxy:armhf "Get your own image badge on microbadger.com")
- `aarch64`: for *64-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy:aarch64.svg)](https://microbadger.com/images/rycus86/webhook-proxy:aarch64 "Get your own image badge on microbadger.com")

`latest` is auto-built on [Docker Hub](https://hub.docker.com/r/rycus86/webhook-proxy)
while the *ARM* builds are uploaded from [Travis](https://travis-ci.org/rycus86/webhook-proxy).

The containers run as a non-root user.

To start the server:

```shell
docker run -d --name=webhook-proxy -p 5000:5000      \
    -v $PWD/server.yml:/etc/conf/webhook-server.yml  \
    rycus86/webhook-proxy:latest                     \
        /etc/conf/webhook-server.yml
```

Or put the configuration file at the default location:

```shell
docker run -d --name=webhook-proxy -p 5000:5000  \
    -v $PWD/server.yml:/app/server.yml           \
    rycus86/webhook-proxy:latest
```

There are 3 more tags available for images that can use the `docker` and `docker-compose`
actions which are running as `root` user:

- `docker`: for *x86* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy:docker.svg)](https://microbadger.com/images/rycus86/webhook-proxy:docker "Get your own image badge on microbadger.com")
- `armhf-docker`: for *32-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy:armhf-docker.svg)](https://microbadger.com/images/rycus86/webhook-proxy:armhf-docker "Get your own image badge on microbadger.com")
- `aarch64-docker`: for *64-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/webhook-proxy:aarch64-docker.svg)](https://microbadger.com/images/rycus86/webhook-proxy:aarch64-docker "Get your own image badge on microbadger.com")

Each of these are built on [Travis](https://travis-ci.org/rycus86/webhook-proxy) and
pushed to [Docker Hub](https://hub.docker.com/r/rycus86/webhook-proxy).

To run these, the _Docker_ daemon's UNIX socket needs to be mounted into the container
too apart from the configuration file:

```shell
docker run -d --name=webhook-proxy -p 5000:5000      \
    -v $PWD/server.yml:/app/server.yml               \
    -v /var/run/docker.sock:/var/run/docker.sock:ro  \
    rycus86/webhook-proxy:docker
```

In _Docker Compose_ on a 64-bit ARM machine the service definition could look like this:

```yaml
version: '2'
services:

  webhooks:
    image: rycus86/webhook-proxy:aarch64
    ports:
      - 8080:5000
    volumes:
      - ./webhook-server.yml:/app/server.yml:ro
```

## Examples

Have a look at the [sample.yml](https://github.com/rycus86/webhook-proxy/blob/master/sample.yml) included in this repo to get
a better idea of the configuration.

You can also find some examples with short explanation below.

- An externally available server listening on port `7000` and printing
  details about a _GitHub_ push webhook

```yaml
server:
  host: '0.0.0.0'
  port: '7000'

endpoints:
  - /github:
      method: 'POST'

      headers:
        X-GitHub-Delivery: '^[0-9a-f\-]+$'
        X-GitHub-Event: 'push'

      body:
        ref: 'refs/heads/.+'
        before: '^[0-9a-f]{40}'
        after: '^[0-9a-f]{40}'
        repository:
          id: '^[0-9]+$'
          full_name: 'sample/.+'
          owner:
            email: '.+@.+\..+'
        commits:
          id: '^[0-9a-f]{40}'
          message: '.+'
          author:
            name: '.+'
          added: '^(src/.+)?'
          removed: '^(src/.+)?'
        pusher:
          name: '.+'
          email: '.+@.+\..+'

      actions:
        - log:
            message: |
              Received a GitHub push from the {{ request.json.repository.full_name }} repo:
              - Pushed by {{ request.json.pusher.name }} <{{ request.json.pusher.email }}>
              - Commits included:
              {% for commit in request.json.commits %}
              +   {{ commit.id }}
              +   {{ commit.committer.name }} at {{ commit.timestamp }}
              +   {{ commit.message }}
              
              {% endfor %}
              Check this change out at {{ request.json.compare }}

        # verify the webhook signature
        - github-verify:
            secret: '{{ read_config("GITHUB_SECRET", "/var/run/secrets/github") }}'
```

The validators for the `/github` endpoint require that
the `X-GitHub-Delivery` header is hexadecimal separated by dashes and
the `X-GitHub-Event` header has the `push` value.
The event also has to come from one of the repos under the `sample` namespace.
Some of the commit hashes are checked that they are 40 character long
hexadecimal values and the commit author's name has to be non-empty.
The `commits` field is actually a list in the _GitHub_ webhook so
the validation is applied to each commit data individually.
The `added` and `removed` checks for example accept if the commit has
not added or removed anything but if it did it has to be in the `src` folder.

For valid webhooks the repository's name, the pushers name and emails are
printed to the standard output followed by the ID, committer name, timestamp
and message of each commit in the push.
The last line displays the URL for the _GitHub_ compare page for the change.


For more information about using the _Jinja2_ templates have a look
at the [official documentation](http://jinja.pocoo.org).

The `github-verify` action will make sure that the webhook is signed as appropriate.
The _secret_ for this is read either from the `/var/run/secrets/github` file or
the `GITHUB_SECRET` environment variable.

> In case it is in a file, that file should contain key-value pairs, like `GITHUB_SECRET=TopSecret`

- Update a _Docker Compose_ project on image changes

Let's assume we have a _Compose_ project with a few services.
When their image is updated in _Docker Hub_ we want to pull it
and get _Compose_ to restart the related containers.

```yaml
server:
  host: '0.0.0.0'
  port: '5000'

endpoints:
  - /webhook/dockerhub:
      method: 'POST'

      body:
        repository:
          repo_name: 'somebody/.+'
          owner: 'somebody'
        push_data:
          tag: 'latest'
      
      actions:
        - docker:
            $containers:
              $list:
            output: |
              {% for container in result if request.json.repository.repo_name in container.image.tags %}
                Found {{ container.name }} with {{ container.image }}
              {% else %}
                {% set _ = error('No containers found using %s'|filter(request.json.repo_name)) %}
              {% endfor %}
        - docker:
            $images:
              $pull:
                repository: '{{ request.json.repo_name }}'
                tag: '{{ request.json.tag }}'
        - docker-compose:
            project_name: 'autoupdate'
            directory: '/var/compose/project'
            $up:
              detached: true
            output: |
              Containers affected:
              {% for container in result %}
              {{ container.name }} <{{ container.short_id }}>
```

The `/webhook/dockerhub` endpoint will accept webhooks from `somebody/*` repos
when an image's `latest` tag is updated.
First a `docker` action checks that we already have containers running that
use the image then another `docker` action pulls the updated image and
finally the `docker-compose` action applies the changes by restarting
any related containers.
