variable "project_id" {
  type        = string
  description = "GCP project id (e.g. switchboard-prod)"
}

variable "region" {
  type    = string
  default = "europe-west4"
}

variable "github_repo" {
  type        = string
  description = "owner/repo (e.g. AlbinLycksell/BOKOMATEN)"
}

variable "postgres_tier" {
  type        = string
  description = "Cloud SQL machine tier"
  default     = "db-custom-1-3840"
}

variable "postgres_app_password" {
  type        = string
  sensitive   = true
  description = "Application role password (switchboard_app)"
}

variable "app_image" {
  type        = string
  description = "Artifact Registry image for application backend"
  default     = "europe-west4-docker.pkg.dev/PROJECT/switchboard/app:latest"
}

variable "bridge_image" {
  type        = string
  description = "Artifact Registry image for realtime bridge"
  default     = "europe-west4-docker.pkg.dev/PROJECT/switchboard/bridge:latest"
}

variable "app_domain" {
  type    = string
  default = "app.switchboard.se"
}

variable "bridge_domain" {
  type    = string
  default = "bridge.switchboard.se"
}

variable "initial_secrets" {
  type        = map(string)
  description = "Map of secret-name → initial value. Empty values create the secret without a version."
  default = {
    "database-url"           = ""
    "bridge-internal-token"  = ""
    "elks-api-username"      = ""
    "elks-api-password"      = ""
    "sentry-dsn"             = ""
  }
  sensitive = true
}
