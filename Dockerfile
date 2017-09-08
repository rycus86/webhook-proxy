FROM alpine

LABEL maintainer "Viktor Adam <rycus86@gmail.com>"

RUN apk --no-cache add python py2-pip

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN adduser -S webapp
USER webapp

ADD src /app
WORKDIR /app

ENTRYPOINT [ "python", "app.py"]