# Local Development with Docker

Prerequisites:
- A local docker environment.

## Steps

1. Clone the repository locally.
2. Enter the ourchive directory: `cd ourchive_app`.
3. Run `docker compose up -d` to bring up containers.
4. Load the fixtures: `docker compose run --rm web ./load-fixtures.sh`
5. Create a superuser:
	a. Run `docker compose exec -it web /bin/bash`
	b. Run `python manage.py createsuperuser`
6. Visit `http://localhost:8000`. Verify that it works!

You should now be able to make modifications to your local files, and the development server should reflect those changes (though it may take a few seconds for the server to reload).

## Debugging

### View Logs

Run `docker compose logs` for both DB and webserver logs.

Run `docker compose logs web` for web logs.


### Get a Docker Shell

Run `docker compose exec -it web /bin/bash` to get a shell onto the docker container.

Once there, you can run `manage.py` commands and other debugging tools.


## Clear the Database

You can delete the database by running `sudo rm -rf data` from the `ourchive_app` directory. Be sure you know what you're doing.
