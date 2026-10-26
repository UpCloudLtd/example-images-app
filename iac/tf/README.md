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

Note that downloading the AI model will take a few minutes, so it is not available immediately after applying the configuration. Before the model is available, the images are generated with a built-in placeholder.

## Use with non-GPU worker nodes

The `worker_plan` variable defaults to non-GPU plan. When you run `tofu apply` without setting the `worker_plan` variable, the configuration will use non-GPU worker nodes.

```sh
tofu apply
```

In this case the AI model will not be used, and the images will be generated with the built-in placeholder.
