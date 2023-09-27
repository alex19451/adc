FROM nginx:latest

RUN mkdir /etc/nginx/ssl

COPY nginx.crt nginx.key /etc/nginx/ssl/

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY htpasswd /etc/nginx/

EXPOSE 443
