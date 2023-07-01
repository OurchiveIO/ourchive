# Auth

## MVP State

Currently, Ourchive uses Django authentication. This means that any app attempting to call the API from a different service will not work. This is a known, temporary limitation to the software: we decided MVP meant people using the frontend that ships with the app would be able to log in.

## Future Stage

Ourchive will implement Django Rest Framework's recommended library, [Django OAuth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/rest-framework/getting_started.html), for token-based auth. This will allow us to support true headless implementations and third-party clients.

If you want to implement this, please do! Drop a PR and we'll merge.