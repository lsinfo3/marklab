#!/bin/bash

export $(grep '^POSTGRES' .env | xargs)
docker compose exec marklab_database psql $POSTGRES_DB $POSTGRES_USER
