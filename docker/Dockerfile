FROM python:3.12-slim
LABEL maintainer="getourchive@gmail.com"

# Avoid prompting for configuration
ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

# Use a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Get the code
COPY --from=root ./ourchive_app /ourchive_app
COPY entrypoint.sh /ourchive_app
WORKDIR /ourchive_app
RUN ls

# grab gosu for easy step-down from root
# https://github.com/tianon/gosu/blob/master/INSTALL.md
ENV GOSU_VERSION 1.12

RUN set -eux; \
    apt-get update; \
    # install system dependencies
    apt-get install -y \
       build-essential \
       gettext \
       # libpq5 needed in runtime for psycopg2
       libpq5 \
       libpq-dev \
       git \
       net-tools \
       procps \
       wget; \
    # install gosu
    apt-get install -y --no-install-recommends ca-certificates wget; \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
    wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
	wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
    chmod +x /usr/local/bin/gosu; \
    # verify gosu signature
    export GNUPGHOME="$(mktemp -d)"; \
	gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
	gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
	command -v gpgconf && gpgconf --kill all || :; \
	rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
    python -m pip install --upgrade pip; \
    python -m pip install wheel


RUN python -m pip install -r requirements.txt; \
    python manage.py compilemessages; \
    python manage.py collectstatic --no-input; \
    chmod +x entrypoint.sh; \
    # cp docker/config.py settings/config.py; \
    #  create ourchive group and user to use it and give permissions over the code (in entrypoint)
    groupadd --system ourchive --gid=999; \
    useradd --system --no-create-home --gid ourchive --uid=999 --shell=/bin/bash ourchive; \
    mkdir -p tmp; \
    mkdir -p media; \
    chown -R ourchive:ourchive /ourchive_app; \
    chmod 755 /ourchive_app


       # remove unneeded files and packages
RUN    apt-get purge -y \
       build-essential \
       gettext \
       git \
       libpq-dev \
       net-tools \
       procps \
       wget; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*; \
    rm -rf /root/.cache; \
    # clean ourchive
    rm requirements.txt; \
    rm ourchive.log; \
    rm -f ourchive_app/.env; \
    find . -name '__pycache__' -exec rm -r '{}' +; \
    find . -name '*pyc' -exec rm -r '{}' +; \
    find . -name '*po' -exec rm -r '{}' +

ENV DJANGO_SETTINGS_MODULE=ourchive_app.settings.base

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]