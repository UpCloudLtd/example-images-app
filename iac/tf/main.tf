module "infra" {
  source = "./upcloud-infra"

  lb_plan     = "essentials"
  url         = var.url
  worker_plan = var.worker_plan
}

module "app" {
  source = "./kubernetes-app"

  app_version   = var.app_version
  registry_base = var.registry_base

  enable_generator  = startswith(var.worker_plan, "GPU-")
  pvc_storage_class = "upcloud-block-storage-maxiops"

  db_connect_url = module.infra.db_connect_url

  objsto_host       = module.infra.objsto.host
  objsto_access_key = module.infra.objsto.access_key
  objsto_secret_key = module.infra.objsto.secret_key

  frontend_service_annotations = module.infra.service_annotations
}
