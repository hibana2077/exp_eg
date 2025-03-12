# Deployment

## Environment Variables

Please copy `.env-template` to `.env` and change the values accordingly.
Also, make sure modify the `minio-config.json` file to match your MinIO configuration.

## Infinity DB config

The config file is located at `src/infinity_conf.toml`, it well be used to configure the Infinity DB server.
Please review the file and change the values accordingly.

[Original Infinity DB config](https://github.com/infiniflow/infinity/blob/main/docs/references/configurations.mdx#a-configuration-file-example)

## Auto Script

After setting up the environment variables, you can run the following command to start the server:

```bash
bash ./setup.sh
```