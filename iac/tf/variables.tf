variable "url" {
  type    = string
  default = ""
}

variable "registry_base" {
  type    = string
  default = ""
}

variable "app_version" {
  type    = string
  default = "latest"
}

variable "worker_plan" {
  type        = string
  description = "Use GPU plan to enable model based image generation."
  default     = "STARTER-2xCPU-4GB"
}
