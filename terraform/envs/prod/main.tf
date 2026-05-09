terraform {
  required_version = ">= 1.9"

  backend "gcs" {
    # Configure via -backend-config; see ../../backend.tfvars.example.
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

module "project" {
  source     = "../../modules/project"
  project_id = var.project_id
  region     = var.region
}

module "network" {
  source     = "../../modules/network"
  project_id = var.project_id
  region     = var.region
  depends_on = [module.project]
}

module "postgres" {
  source            = "../../modules/postgres"
  project_id        = var.project_id
  region            = var.region
  tier              = var.postgres_tier
  network_self_link = module.network.network_self_link
  app_password      = var.postgres_app_password
  depends_on        = [module.network]
}

module "storage" {
  source     = "../../modules/storage"
  project_id = var.project_id
  region     = var.region
  depends_on = [module.project]
}

module "secrets" {
  source         = "../../modules/secrets"
  project_id     = var.project_id
  initial_values = var.initial_secrets
  depends_on     = [module.project]
}

module "workload_identity" {
  source           = "../../modules/workload_identity"
  project_id       = var.project_id
  github_repo      = var.github_repo
  service_accounts = ["switchboard-app", "switchboard-bridge"]
  depends_on       = [module.project]
}

module "cloud_run_backend" {
  source            = "../../modules/cloud_run"
  project_id        = var.project_id
  region            = var.region
  name              = "switchboard-app"
  image             = var.app_image
  min_instances     = 0
  max_instances     = 10
  cpu               = "1"
  memory            = "1Gi"
  service_account   = module.workload_identity.service_account_emails["switchboard-app"]
  vpc_connector     = module.network.vpc_connector_id
  domain            = var.app_domain
  request_timeout_s = 300
  env = {
    SWITCHBOARD_ENV                = "prod"
    SWITCHBOARD_REGION             = var.region
    SWITCHBOARD_LOG_JSON           = "true"
    SWITCHBOARD_GEMINI_PROVIDER    = "vertex"
    SWITCHBOARD_VERTEX_PROJECT     = var.project_id
    SWITCHBOARD_VERTEX_LOCATION    = var.region
    SWITCHBOARD_AUTH_MODE          = "jwks"
    SWITCHBOARD_AUTH_JWKS_URL      = "https://${var.app_domain}/api/auth/jwks"
    SWITCHBOARD_AUTH_AUDIENCE      = "switchboard-backend"
    SWITCHBOARD_AUTH_ISSUER        = "https://${var.app_domain}"
    SWITCHBOARD_STORAGE_MODE       = "gcs"
    SWITCHBOARD_GCP_PROJECT        = var.project_id
    SWITCHBOARD_GCS_BUCKET_PREFIX  = "switchboard-rec"
    SWITCHBOARD_KMS_KEYRING        = module.storage.keyring_name
    SWITCHBOARD_KMS_LOCATION       = var.region
    SWITCHBOARD_TOOL_DISPATCH_MODE = "local"
  }
  secret_env = {
    SWITCHBOARD_DATABASE_URL          = module.secrets.refs["database-url"]
    SWITCHBOARD_BRIDGE_INTERNAL_TOKEN = module.secrets.refs["bridge-internal-token"]
    SWITCHBOARD_ELKS_API_USERNAME     = module.secrets.refs["elks-api-username"]
    SWITCHBOARD_ELKS_API_PASSWORD     = module.secrets.refs["elks-api-password"]
    SENTRY_DSN                   = module.secrets.refs["sentry-dsn"]
  }
  depends_on = [module.postgres, module.workload_identity]
}

module "cloud_run_bridge" {
  source            = "../../modules/cloud_run"
  project_id        = var.project_id
  region            = var.region
  name              = "switchboard-bridge"
  image             = var.bridge_image
  min_instances     = 2
  max_instances     = 20
  cpu               = "1"
  memory            = "2Gi"
  service_account   = module.workload_identity.service_account_emails["switchboard-bridge"]
  vpc_connector     = module.network.vpc_connector_id
  domain            = var.bridge_domain
  request_timeout_s = 3600
  env = {
    SWITCHBOARD_ENV                    = "prod"
    SWITCHBOARD_REGION                 = var.region
    SWITCHBOARD_LOG_JSON               = "true"
    SWITCHBOARD_GEMINI_PROVIDER        = "vertex"
    SWITCHBOARD_VERTEX_PROJECT         = var.project_id
    SWITCHBOARD_VERTEX_LOCATION        = var.region
    SWITCHBOARD_TOOL_DISPATCH_MODE     = "http"
    SWITCHBOARD_APPLICATION_BACKEND_URL = "https://${var.app_domain}"
    SWITCHBOARD_STORAGE_MODE           = "gcs"
    SWITCHBOARD_GCP_PROJECT            = var.project_id
    SWITCHBOARD_GCS_BUCKET_PREFIX      = "switchboard-rec"
    SWITCHBOARD_KMS_KEYRING            = module.storage.keyring_name
    SWITCHBOARD_KMS_LOCATION           = var.region
  }
  secret_env = {
    SWITCHBOARD_DATABASE_URL          = module.secrets.refs["database-url"]
    SWITCHBOARD_BRIDGE_INTERNAL_TOKEN = module.secrets.refs["bridge-internal-token"]
    SENTRY_DSN                   = module.secrets.refs["sentry-dsn"]
  }
  depends_on = [module.postgres, module.workload_identity]
}
