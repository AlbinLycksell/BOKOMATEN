variable "project_id" { type = string }
variable "github_repo" { type = string }
variable "service_accounts" { type = list(string) }

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"      = "assertion.actor"
    "attribute.ref"        = "assertion.ref"
  }
  attribute_condition = "assertion.repository == \"${var.github_repo}\""
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "svc" {
  for_each     = toset(var.service_accounts)
  project      = var.project_id
  account_id   = each.key
  display_name = each.key
}

resource "google_service_account_iam_member" "wif" {
  for_each = google_service_account.svc
  service_account_id = each.value.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# Minimum permissions per service per least-privilege.
locals {
  service_roles = {
    "svarsa-app" = [
      "roles/run.invoker",
      "roles/cloudsql.client",
      "roles/secretmanager.secretAccessor",
      "roles/storage.objectAdmin",
      "roles/cloudkms.cryptoKeyEncrypterDecrypter",
      "roles/aiplatform.user",
      "roles/cloudtrace.agent",
    ]
    "svarsa-bridge" = [
      "roles/run.invoker",
      "roles/cloudsql.client",
      "roles/secretmanager.secretAccessor",
      "roles/storage.objectAdmin",
      "roles/cloudkms.cryptoKeyEncrypterDecrypter",
      "roles/aiplatform.user",
      "roles/cloudtrace.agent",
    ]
  }

  flat_roles = flatten([
    for sa, roles in local.service_roles : [
      for role in roles : { sa = sa, role = role }
    ]
  ])
}

resource "google_project_iam_member" "svc_role" {
  for_each = { for r in local.flat_roles : "${r.sa}-${r.role}" => r }
  project  = var.project_id
  role     = each.value.role
  member   = "serviceAccount:${google_service_account.svc[each.value.sa].email}"
}

output "service_account_emails" {
  value = { for k, v in google_service_account.svc : k => v.email }
}

output "pool_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}
