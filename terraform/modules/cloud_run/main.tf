variable "project_id" { type = string }
variable "region" { type = string }
variable "name" { type = string }
variable "image" { type = string }
variable "service_account" { type = string }
variable "min_instances" { type = number }
variable "max_instances" { type = number }
variable "cpu" { type = string }
variable "memory" { type = string }
variable "vpc_connector" { type = string }
variable "domain" { type = string }
variable "request_timeout_s" { type = number }
variable "env" {
  type    = map(string)
  default = {}
}
variable "secret_env" {
  type    = map(string)
  default = {}
}

resource "google_cloud_run_v2_service" "svc" {
  name     = var.name
  project  = var.project_id
  location = var.region

  template {
    service_account = var.service_account
    timeout         = "${var.request_timeout_s}s"
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    vpc_access {
      connector = var.vpc_connector
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.image
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle = true
      }

      ports {
        container_port = 8080
      }

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = element(split("/", env.value), 3)
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,  # image rolls via gh actions, not terraform
    ]
  }
}

resource "google_cloud_run_domain_mapping" "domain" {
  count    = var.domain != "" ? 1 : 0
  name     = var.domain
  location = var.region
  project  = var.project_id
  metadata {
    namespace = var.project_id
  }
  spec {
    route_name = google_cloud_run_v2_service.svc.name
  }
}

output "url" {
  value = google_cloud_run_v2_service.svc.uri
}

output "service_name" {
  value = google_cloud_run_v2_service.svc.name
}
