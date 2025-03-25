# Deployment

## TL;DR

```bash
cp .env-template .env
bash ./install_everything.sh
bash ./setup.bash # or sudo bash ./setup.sh
docker-compose up -d --build
```

## Environment Variables

Please copy `.env-template` to `.env` and change the values accordingly.
Also, make sure modify the `minio-config.json` file to match your MinIO configuration.

## Infinity DB config

The config file is located at `src/infinity_conf.toml`, it well be used to configure the Infinity DB server.
Please review the file and change the values accordingly.

[Original Infinity DB config](https://github.com/infiniflow/infinity/blob/main/docs/references/configurations.mdx#a-configuration-file-example)

## Auto Script

After setting up the environment variables and config, you can run the following command to put config to the right place:

```bash
bash ./setup.sh
```