# Infrastructure / Docker

This directory is reserved for reusable Docker support assets and deployment-specific configuration.

Typical contents include:

- custom Dockerfiles for service variants
- healthcheck scripts
- deployment manifests
- environment templates
- service-specific startup files
- image build helpers

The root `docker-compose.yml` currently serves as the primary orchestration entry point, so this directory remains intentionally minimal for now.
