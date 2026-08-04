From ubuntu:latest
WORKDIR ./app/project
COPY . .
CMD["php","artisan","serve"]
