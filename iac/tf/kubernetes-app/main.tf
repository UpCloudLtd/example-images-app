terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  lb_url = "https://${kubernetes_service.frontend.status[0].load_balancer[0].ingress[0].hostname}"
}

resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
  }
}

resource "random_password" "generator_token" {
  count = var.enable_generator ? 1 : 0

  length  = 32
  special = false
}

resource "kubernetes_secret" "generator" {
  count = var.enable_generator ? 1 : 0

  metadata {
    name      = "generator"
    namespace = var.namespace
  }

  data = {
    token = random_password.generator_token[0].result
  }
}

resource "kubernetes_secret" "backend" {
  metadata {
    name      = "backend"
    namespace = var.namespace
  }

  data = {
    database_url      = var.db_connect_url
    objsto_access_key = var.objsto_access_key
    objsto_secret_key = var.objsto_secret_key
  }
}

resource "kubernetes_deployment" "backend" {
  metadata {
    name      = "backend"
    namespace = var.namespace
    labels = {
      app = "backend"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "backend"
      }
    }

    template {
      metadata {
        labels = {
          app = "backend"
        }
      }

      spec {
        container {
          image = "${var.registry_base}backend:${var.app_version}"
          name  = "backend"

          port {
            container_port = 5000
          }

          env {
            name = "DATABASE_URL"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.backend.metadata[0].name
                key  = "database_url"
              }
            }
          }

          env {
            name = "OBJSTO_ACCESS_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.backend.metadata[0].name
                key  = "objsto_access_key"
              }
            }
          }

          env {
            name = "OBJSTO_SECRET_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.backend.metadata[0].name
                key  = "objsto_secret_key"
              }
            }
          }

          env {
            name  = "OBJSTO_ENDPOINT_URL"
            value = "https://${var.objsto_host}"
          }

          env {
            name  = "OBJSTO_BUCKET"
            value = var.objsto_bucket
          }

          env {
            name  = "AWS_REQUEST_CHECKSUM_CALCULATION"
            value = "when_required"
          }

          env {
            name  = "AWS_RESPONSE_CHECKSUM_VALIDATION"
            value = "when_required"
          }

          dynamic "env" {
            for_each = kubernetes_secret.generator
            content {
              name = "GENERATOR_TOKEN"
              value_from {
                secret_key_ref {
                  name = env.value.metadata[0].name
                  key  = "token"
                }
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "backend" {
  metadata {
    name      = "backend"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = "backend"
    }

    port {
      port        = 5000
      target_port = 5000
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_deployment" "frontend" {
  metadata {
    name      = "frontend"
    namespace = var.namespace
    labels = {
      app = "frontend"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "frontend"
      }
    }

    template {
      metadata {
        labels = {
          app = "frontend"
        }
      }

      spec {
        container {
          image = "${var.registry_base}frontend:${var.app_version}"
          name  = "frontend"

          port {
            container_port = 80
          }

          env {
            name  = "BACKEND_URL"
            value = "http://${kubernetes_service.backend.metadata[0].name}:5000"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "frontend" {
  metadata {
    name        = "frontend"
    namespace   = var.namespace
    annotations = var.frontend_service_annotations
  }

  spec {
    selector = {
      app = "frontend"
    }

    port {
      port        = 443
      target_port = 80
    }

    type = "LoadBalancer"
  }
}

resource "helm_release" "nvidia_device_plugin" {
  count = var.enable_generator ? 1 : 0

  name             = "nvidia-device-plugin"
  repository       = "https://nvidia.github.io/k8s-device-plugin"
  chart            = "nvidia-device-plugin"
  namespace        = "nvidia-device-plugin"
  create_namespace = true
}

resource "kubernetes_persistent_volume_claim" "models" {
  count = var.enable_generator ? 1 : 0

  metadata {
    name      = "models"
    namespace = var.namespace
  }

  spec {
    storage_class_name = var.pvc_storage_class != "" ? var.pvc_storage_class : null
    access_modes       = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "30Gi"
      }
    }
  }

  # The volume may stay unbound until the generator pod is scheduled.
  wait_until_bound = false
}

resource "kubernetes_deployment" "generator" {
  count = var.enable_generator ? 1 : 0

  depends_on = [helm_release.nvidia_device_plugin]

  metadata {
    name      = "generator"
    namespace = var.namespace
    labels = {
      app = "generator"
    }
  }

  spec {
    # ReadWriteOnce volume cannot be attached to the old and new pod at the same time.
    strategy {
      type = "Recreate"
    }

    selector {
      match_labels = {
        app = "generator"
      }
    }

    template {
      metadata {
        labels = {
          app = "generator"
        }
      }

      spec {
        container {
          image = "${var.registry_base}generator:${var.app_version}"
          name  = "generator"

          env {
            name  = "BACKEND_URL"
            value = "http://${kubernetes_service.backend.metadata[0].name}:5000"
          }

          env {
            name = "GENERATOR_TOKEN"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.generator[0].metadata[0].name
                key  = "token"
              }
            }
          }

          env {
            name  = "HF_HOME"
            value = "/models"
          }

          resources {
            limits = {
              "nvidia.com/gpu" = "1"
            }
          }

          volume_mount {
            name       = "models"
            mount_path = "/models"
          }
        }

        volume {
          name = "models"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.models[0].metadata[0].name
          }
        }
      }
    }
  }
}
