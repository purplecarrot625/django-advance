# base image
FROM python:3.9-alpine3.13
# maintener
LABEL maintainer="Buzzstudio.com"

# don't buffer the output of python
ENV PYTHONUNBUFFERED 1

# local machine to docker image
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false

# install
# new virtual environment
RUN python -m venv /py && \
# upgrade the python manager in the virtual environment
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    # install the requirements inside the docker image
    /py/bin/pip install -r /tmp/requirements.txt && \
    # remove the tmp files before the end of the docker file
    if [ "$DEV" = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    # delete the build dependencies
    apk del .tmp-build-deps && \
    # add new user inside the image, not use the root user
    adduser \
        --disabled-password \
        # not create home directory
        --no-create-home \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

# path is auto created by linux, we don't need to include the full path each time
ENV PATH="/py/bin:$PATH"

USER django-user
