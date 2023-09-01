[![Deploy Dev App](https://github.com/c-e-p/ourchive/actions/workflows/deploy_dev_app.yml/badge.svg?branch=development)](https://github.com/c-e-p/ourchive/actions/workflows/deploy_dev_app.yml)

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

see [local-dev](local-dev.md) for further local dev set up.


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

We have used Unsplash free images for icon defaults.

This app was instantiated in part from the [flask boilerplate](https://github.com/italomaia/flask-empty) project, as well as [react-flask](https://github.com/bonniee/react-flask). Additionally, all the frameworks and tools we are using are open source, including:

- tusd
- React
- flask
- postgres
- docker
- redis
- elasticsearch
- pytest
