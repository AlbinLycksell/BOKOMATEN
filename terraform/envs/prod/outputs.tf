output "app_url" {
  value = module.cloud_run_backend.url
}

output "bridge_url" {
  value = module.cloud_run_bridge.url
}

output "postgres_connection_name" {
  value = module.postgres.connection_name
}

output "service_accounts" {
  value = module.workload_identity.service_account_emails
}

output "kms_keyring" {
  value = module.storage.keyring_name
}
