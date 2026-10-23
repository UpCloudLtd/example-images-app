# OpenTofu/Terraform modules

This directory contains modules for creating a Kubernetes cluster and Object Storage as well as deploying the application to a Kubernetes cluster. See [main.tf](./main.tf) for examples usage.

Until the images are available in this repository, you need to build and push the images yourself. Use `registry_base` variable to specify the base URL of your container registry.
