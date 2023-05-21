[![Build Status](https://travis-ci.org/c-e-p/ourchive.svg?branch=travis-ci)](https://travis-ci.org/c-e-p/ourchive)

# ourchive

Ourchive is a configurable, multi-media archive application. It grew out of a need for archival web apps that focus on browsability and searchability, and are able to be easily installed and maintained by a non-technical administrator.

<!-- MarkdownTOC -->

- [installation](#installation)
- [contributor guidelines](#contributor-guidelines)
    - [ways to contribute](#ways-to-contribute)
- [code of conduct](#code-of-conduct)

<!-- /MarkdownTOC -->

<a name="installation"></a>
## installation

### Stack

Ourchive runs on Django, using Django Rest Framework for the backend. The following stack is recommended:

Host: Debian Linux
Database: Postgres
Task scheduler: Django Background Tasks
Search: Postgres OR Elastic (configurable provider)
File Upload: Django OR S3 (configurable provider)

Postgres will need to be up and running.

FFMPEG should be installed on the Linux machine to enable audio processing.

Things to run:

```python manage.py migrate```
```python manage.py loaddata settings```

Without loading data from the settings fixture, you may encounter errors when the system tries to pull default settings by name.

### Docker Container Development

we have a [Dockerfile](Dockerfile), and a [docker-compose.yml](docker-compose.yml) that creates a container with a db service (currently hardcoded to postgres) and a web service that runs the django app. 

1. in the repo root, build the image
    `docker build .`
2. in the repo root, run the docker compose
    `docker-compose up` (or `docker-compose up -d` to run detached)
    run
    `docker-compose -f docker-compose-tests.override.yml up` 
    if you want to run the ui tests.
3. navigate to your `localhost:8000` on your local machine and you should see the webapp running!!!

> note: if on windows, you may find that you need to use `http://host.docker.internal:8000/` instead. If you are having issues, check your hosts file and make sure your docker install hasn't screwed up the hosts file with a bunch of duplicative garbage.

### How to Run the UI Tests

we're using [pytest](), and [selenium]() to power the ui tests, with special thanks for the python [webdriver_manager]() package because i hate dealing with selenium driver dependancies.

to run the ui tests, please have the docker compose tests container running.
>    if you are not using the default location, change the `baseURL` in [ui_tests/__init__.py](ui_tests\__init__.py) to where it is)

you can run all the ui tests by running:
`python -m ui_tests/run_tests.py`
This will run the tests against both Chrome and Firefox.

or you can run them from the command line with pytest:
`pytest ui_test --browser=CHROME`

the browser flag controls what browser the ui tests are run in; if not supplied, it defaults to chrome. 

currently supported browsers:
- chrome
- firefox

### Dependencies

<a name="contributor-guidelines"></a>
## contributor guidelines

<a name="ways-to-contribute"></a>
### ways to contribute

- USE THIS APP! spin up an archive, play around with it, and when you run into issues, please log them as [github issues]()! [good bug reporting guidelines](https://www.joelonsoftware.com/2000/11/08/painless-bug-tracking/)
- Tell others about this app - word of mouth is always helpful.

We welcome technical contributions as well:

- Submit a code fix for a bug. Grab a bug out of the [issue tracker]() and fix that sucker! Then make a pull request to the repo. [pull request guidelines]()
- Submit a new feature request [as a GitHub issue]().
- Work on a feature that's on the roadmap, or unassigned in [the release version]()! Then make a pull request to the repo. [pull request guidelines]()
- Submit a unit test.
- Submit another unit test. Maybe even a ui test if you're feeling frisky!

Please see the [wiki](https://github.com/c-e-p/ourchive/wiki) for more on technical contributions, PR guidelines, and so on.

(ganked with love from [azure](https://azure.github.io/guidelines/))


<a name="code-of-conduct"></a>
## code of conduct

Please see [the code of conduct and diversity statement](codeofconduct.md).

## thanks

This app was instantiated in part from the [flask boilerplate](https://github.com/italomaia/flask-empty) project, as well as [react-flask](https://github.com/bonniee/react-flask). Additionally, all the frameworks and tools we are using are open source, including:

- tusd
- React
- flask
- postgres
- docker
- redis
- elasticsearch
- pytest
