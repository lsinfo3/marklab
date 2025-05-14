FROM nginx:1.27

RUN rm /etc/nginx/conf.d/default.conf
COPY marklab.conf /etc/nginx/conf.d/marklab.conf

WORKDIR /marklab_proxy
ADD cert.pem key.pem ./
