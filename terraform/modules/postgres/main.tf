variable "project_id" { type = string }
variable "region" { type = string }
variable "tier" { type = string }
variable "network_self_link" { type = string }
variable "app_password" {
  type      = string
  sensitive = true
}

resource "google_sql_database_instance" "primary" {
  name                = "switchboard-pg"
  project             = var.project_id
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = true

  settings {
    tier              = var.tier
    availability_type = "ZONAL"
    disk_autoresize   = true
    disk_size         = 20

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      start_time                     = "02:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_self_link
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "500"
    }
  }
}

resource "google_sql_database" "switchboard" {
  name     = "switchboard"
  project  = var.project_id
  instance = google_sql_database_instance.primary.name
}

resource "google_sql_user" "app" {
  name     = "switchboard_app"
  project  = var.project_id
  instance = google_sql_database_instance.primary.name
  password = var.app_password
}

output "connection_name" {
  value = google_sql_database_instance.primary.connection_name
}

output "private_ip" {
  value = google_sql_database_instance.primary.private_ip_address
}
