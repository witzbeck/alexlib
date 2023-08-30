Sure, here's an example of a Docker Compose script that starts a container with an instance of PostgreSQL:

```yaml
version: '3.8'
services:
  db:
    image: postgres
    restart: always
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydatabase
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

To run this script, save it to a file named `docker-compose.yml`, and then you can start the container using the following command:

```
docker-compose up -d
```

This will start a container with PostgreSQL running on the default port (5432). The database will be initialized with the provided environmental variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`), and the data will be persisted in a volume named `pgdata`.

You can access the PostgreSQL instance using your preferred tool, connecting to `localhost:5432`. Make sure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine before running this script.