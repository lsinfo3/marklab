FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends openssh-client

WORKDIR /marklab_web

ADD requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

ADD . .

RUN python3 manage.py collectstatic -c --no-input

ENTRYPOINT [ "gunicorn", "--workers", "3", "--timeout", "600", "--bind", "0.0.0.0:80", "marklab.wsgi" ]
