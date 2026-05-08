variable "project_id" { type = string }
variable "initial_values" {
  type      = map(string)
  sensitive = true
}

resource "google_secret_manager_secret" "secret" {
  for_each  = var.initial_values
  project   = var.project_id
  secret_id = each.key
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "version" {
  for_each = {
    for k, v in var.initial_values : k => v if v != ""
  }
  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = each.value
}

output "refs" {
  value = {
    for k, s in google_secret_manager_secret.secret :
    k => "projects/${s.project}/secrets/${s.secret_id}/versions/latest"
  }
}
