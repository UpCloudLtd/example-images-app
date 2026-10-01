terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
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
