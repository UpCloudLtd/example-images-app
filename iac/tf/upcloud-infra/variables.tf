variable "prefix" {
  type    = string
  default = "example-images-app-"
}

variable "cidr" {
  type    = string
  default = "172.24.16.0/24"
}

variable "zone" {
  type    = string
  default = "fi-hel2"
}

variable "region" {
  type    = string
  default = "europe-1"
}

variable "worker_plan" {
  type    = string
  default = "STARTER-2xCPU-4GB"
}

variable "db_plan" {
  type    = string
  default = "1x1xCPU-2GB-25GB"
}

// For service annotations
variable "lb_plan" {
  type    = string
  default = "essentials"
}

variable "url" {
  type    = string
  default = ""
}
