[![Deploy Dev App](https://github.com/c-e-p/ourchive/actions/workflows/deploy_dev_app.yml/badge.svg?branch=development)](https://github.com/c-e-p/ourchive/actions/workflows/deploy_dev_app.yml)

# ourchive

Ourchive is a configurable, multi-media archive application. We aim to meet the need for archival web apps that focus on browsability and searchability, and are able to be easily installed and maintained by a non-technical administrator.

<!-- MarkdownTOC -->

- [Links](#links)
- [Installation](#installation)
- [Contributor Guidelines](#contributor-guidelines)
    - [Ways to Contribute](#ways-to-contribute)
- [Code of Conduct](#code-of-conduct)
- [Thanks](#thanks)

<!-- /MarkdownTOC -->

<a name="links"></a>
## Links

- [Project Homepage](https://getourchive.io)
- [Developers](https://developer.getourchive.io)
- [Admin Docs](https://docs.getourchive.io/tag/admin-docs/)
- [Blog](https://docs.getourchive.io/tag/blog/)


<a name="installation"></a>
## Installation

Ourchive runs on Django.

To set up as an admin, check out our documentation's [Getting Started](https://docs.getourchive.io/admin-getting-started/) page.

For local development: [developer docs](https://developer.getourchive.io).


<a name="contributor-guidelines"></a>
## Contributor Guidelines

<a name="ways-to-contribute"></a>
### Ways to Contribute

- USE THIS APP! spin up an archive, play around with it, and when you run into issues, please log them as [github issues][github issues]! [good bug reporting guidelines](https://www.joelonsoftware.com/2000/11/08/painless-bug-tracking/)
- Tell others about this app - word of mouth is always helpful.

We welcome technical contributions as well:

- Submit a code fix for a bug. Grab a bug out of the [issue tracker][github issues] and fix that sucker! Then make a pull request to the repo.
- Submit a new feature request [as a GitHub issue][github issues].
- Work on a feature that's on the roadmap, or unassigned in [the release version](https://planning.ourchive.io/project/ourchive-beta/kanban).
- Submit a unit test.
- Submit another unit test. Maybe even a UI test if you're feeling frisky!

Please see the our [developer docs](https://developer.getourchive.io/docs/contributing/drive-by-contributions/) for more on technical contributions, PR guidelines, and so on.

(ganked with love from [azure](https://azure.github.io/guidelines/))


<a name="code-of-conduct"></a>
## Code of Conduct

Please see [the code of conduct and diversity statement](codeofconduct.md).

<a name="thanks"></a>
## Thanks

We use Unsplash free images for icon defaults.

For test data, we use:
* audio from [Freesound](https://freesound.org/)
* images from [Unsplash](https://unsplash.com/)
* Videos from the [ESO](https://www.eso.org/public/videos/list/4/)

All frameworks and tools we are using are open source, including:

- Django
- Postgres
- Docker
- pytest
- Tabler (icons)
- UIKit (CSS + JS)

[github issues]: https://github.com/c-e-p/ourchive/issues
[pull request template]: .github/PULL_REQUEST_TEMPLATE/pr_feature_template.md
