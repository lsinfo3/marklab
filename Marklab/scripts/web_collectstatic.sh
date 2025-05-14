#!/bin/bash

docker compose exec marklab-web python3 manage.py collectstatic -c --no-input $@
