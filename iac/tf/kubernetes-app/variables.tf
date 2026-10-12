variable "namespace" {
  type    = string
  default = "example-images-app"
}

variable "db_connect_url" {
  type      = string
  sensitive = true
}

variable "registry_base" {
  type    = string
  default = ""
}

variable "objsto_bucket" {
  type    = string
  default = "images"
}

variable "app_version" {
  type    = string
  default = "latest"
}

variable "objsto_host" {
  type    = string
  default = ""
}

variable "objsto_access_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "objsto_secret_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "pvc_storage_class" {
  type    = string
  default = ""
}

variable "enable_generator" {
  type        = bool
  description = "Deploy the image generator. Requires a node with a GPU."
  default     = false
}

variable "frontend_service_annotations" {
  type    = map(string)
  default = {}
}
