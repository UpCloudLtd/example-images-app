# OpenTofu/Terraform modules

This directory contains modules for creating a Kubernetes cluster and Object Storage as well as deploying the application to a Kubernetes cluster. See [main.tf](./main.tf) for examples usage.

First, install required providers by running `tofu init`:

```sh
tofu init
```

## Use GPU worker nodes

To enable GPU worker nodes (and usage of an AI model) set the `worker_plan` variable to a plan that includes GPU support. For example:

```sh
export TF_VAR_worker_plan="GPU-8xCPU-64GB-1xL40S"
tofu apply
```
