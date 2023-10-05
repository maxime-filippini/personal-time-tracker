# Simple time tracker

## Install the package

```console
$ git clone ...
$ cd time-tracker
$ pip install -e .
```

## Initialize the SQLite database

```console
$ python -m timetracker.server.db
```

Once initialized, the database will be located in `$HOME/.timetracker`.

## Run the server locally

```console
$ python -m timetracker-server --port 8000 --reload
```
