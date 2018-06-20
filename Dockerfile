ARG BASE_IMAGE="alpine"

FROM $BASE_IMAGE

LABEL maintainer "Viktor Adam <rycus86@gmail.com>"

RUN apk --no-cache add python py2-pip

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN adduser -S webapp
USER webapp

ADD src /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "python", "app.py"]

# add app info as environment variables
ARG GIT_COMMIT
ENV GIT_COMMIT $GIT_COMMIT
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP $BUILD_TIMESTAMP
