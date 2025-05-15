# Marklab

## Setup

Create a `.env` file with the following contents in the current directory:

```bash
# Django database configuration (these values must be the same as in the PostgreSQL section)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=marklab
DATABASE_USER=marklab
DATABASE_PASSWORD=...
DATABASE_HOST=marklab_database
DATABASE_PORT=5432

# Django secret key (the command below can generate this)
# python3 -c "import secrets; print(secrets.token_urlsafe(128))"
DJANGO_SECRET_KEY=

# Whether to enable Django debug mode
DJANGO_DEBUG=false

# Comma-separated list of Django allowed hosts
# IP addresses and hostnames assigned to the management server must be listed here
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,marklab-web

# Folder where results will be stored on the host
RESULTS_FOLDER=/home/ubuntu/results

# SSH folder (required for rebooting nodes and uploading Docker images via SSH)
SSH_FOLDER=/home/ubuntu/.ssh

# Superuser credentials for devices (required for rebooting nodes)
DEVICE_USERNAME=ubuntu
DEVICE_PASSWORD=...

# Choose a password/key that will be used to register new nodes
REGISTRATION_KEY=...

# PostgreSQL configuration
POSTGRES_USER=marklab
POSTGRES_PASSWORD=...
POSTGRES_DB=marklab
```

If TLS is desired, supply a certificate (`proxy/cert.pem`) and a matching private key (`proxy/key.pem`), otherwise comment out the marklab_proxy section in `docker-compose.yml`.

On the first installation or after an update, the Docker images will have to be rebuilt:

```bash
docker compose build
```

To start the Docker Compose project, execute this command or deploy the provided systemd service (`marklab.service`):

```bash
docker compose up
```

Finally, run the database migrations and create a superuser:

```bash
scripts/web_manage.sh makemigrations
scripts/web_manage.sh migrate
scripts/web_manage.sh createsuperuser
```

## Containers

 - `marklab-web`: Django & Gunicorn
 - `marklab_database`: PostgreSQL
 - `marklab_proxy`: Nginx (optional)
