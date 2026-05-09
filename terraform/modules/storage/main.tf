variable "project_id" { type = string }
variable "region" { type = string }

resource "google_kms_key_ring" "switchboard" {
  name     = "switchboard"
  project  = var.project_id
  location = var.region
}

# Per-tenant CryptoKey is created at firma onboarding by the application
# (see backend/src/switchboard/integrations/storage.py:GCSStorage). The keyring
# itself is the only platform-level resource.

output "keyring_name" {
  value = google_kms_key_ring.switchboard.name
}

output "keyring_id" {
  value = google_kms_key_ring.switchboard.id
}
