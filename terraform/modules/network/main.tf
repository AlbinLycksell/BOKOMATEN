variable "project_id" { type = string }
variable "region" { type = string }

resource "google_compute_network" "vpc" {
  name                    = "switchboard-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "default" {
  name                     = "switchboard-subnet"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.vpc.self_link
  ip_cidr_range            = "10.10.0.0/24"
  private_ip_google_access = true
}

resource "google_compute_subnetwork" "connector" {
  name          = "switchboard-conn-subnet"
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.vpc.self_link
  ip_cidr_range = "10.10.1.0/28"
}

resource "google_vpc_access_connector" "connector" {
  name          = "switchboard-connector"
  project       = var.project_id
  region        = var.region
  subnet {
    name = google_compute_subnetwork.connector.name
  }
  machine_type   = "e2-micro"
  min_instances  = 2
  max_instances  = 3
  max_throughput = 300
}

resource "google_compute_global_address" "private_services" {
  name          = "switchboard-private-services"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.self_link
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.vpc.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services.name]
}

output "network_self_link" {
  value = google_compute_network.vpc.self_link
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.connector.id
}
