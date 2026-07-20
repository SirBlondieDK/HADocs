# Docker

Docker is suited to servers, NAS devices, virtual machines, and LXC hosts. It uses the same HADocs analysis engine and web interface as every supported platform.

> [!NOTE]
> `sirblondiedk/hadocs:dev` is currently the only public Docker channel configured by the project. It tracks preview/development builds from `main`; no `latest` channel is published yet.

## Install

Create `docker-compose.yml`:

```yaml
services:
  hadocs:
    image: sirblondiedk/hadocs:dev
    container_name: hadocs

    env_file:
      - ./docker/hadocs.env

    environment:
      HADOCS_OUTPUT_DIR: /output

    volumes:
      - ./docker/output:/output
      - ./docker/cache:/cache
      - ./docker/config:/config

    ports:
      - "8099:8099"

    entrypoint: ["python", "-m", "src.hadocs.web.app"]

    restart: unless-stopped
```

Create the persistent directories:

```bash
mkdir -p docker/output docker/cache docker/config
```

Create `docker/hadocs.env` with your runtime configuration. Do not commit private tokens.

Start HADocs:

```bash
docker compose pull
docker compose up -d
```

Open `http://SERVER-IP:8099`.

## Operate and update

```bash
docker compose logs -f hadocs
```

```bash
docker compose pull
docker compose up -d --force-recreate
```

```bash
docker compose ps
```

The container should remain **Up** because it starts the HADocs web application rather than the one-shot `generate` command.

Next: review [configuration](../../CONFIGURATION.md), or return to the [documentation home](../../README.md).
