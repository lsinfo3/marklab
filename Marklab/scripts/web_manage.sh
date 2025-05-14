#!/bin/bash

docker compose exec marklab-web python3 manage.py $@
