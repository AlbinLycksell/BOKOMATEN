variable "project_id" { type = string }
variable "region" { type = string }

locals {
  required_apis = [
    "run.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtasks.googleapis.com",
    "cloudscheduler.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.required_apis)
  project  = var.project_id
  service  = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "svarsa" {
  project       = var.project_id
  location      = var.region
  repository_id = "svarsa"
  format        = "DOCKER"
  description   = "Svarsa Cloud Run images"
  depends_on    = [google_project_service.enabled]
}
