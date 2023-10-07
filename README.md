# Simple personal time tracker

## To do

- [ ] Implement CRUD for work items
- [ ] Allow to start a timer from an existing entries
- [ ] Make the banded rows consistent when records are deleted
- [ ] Add confirm on page exit when a timer is running

## How to use

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
