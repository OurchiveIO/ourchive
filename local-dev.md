# Local Dev Set Up

Required:

- python 3.x +
- postgres 15+ [docs](https://www.postgresql.org/docs/15/index.html)


## Steps

1. create local [venv](https://docs.python.org/3/library/venv.html) for your repo 
2. activate venv and install required packages from [`requirements.txt`](requirements.txt)

	- if you get an install error for `psycopg2` that references `libpq-fe.h` like so:
	```
	      ./psycopg/psycopg.h:36:10: fatal error: libpq-fe.h: No such file or directory
         36 | #include <libpq-fe.h>
    ```
    check out [this](https://askubuntu.com/questions/1372562/how-to-install-libpq-dev-14-0-1-on-ubuntu-21-10)
3. create a new database to use in postgres