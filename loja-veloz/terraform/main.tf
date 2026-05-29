# ══════════════════════════════════════════════════════════════════════════════
# Terraform — Infraestrutura Loja Veloz (GKE — Google Kubernetes Engine)
# ══════════════════════════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.26"
    }
  }

  # State remoto: evita conflitos em equipe
  backend "gcs" {
    bucket = "loja-veloz-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── VPC e Subnet ──────────────────────────────────────────────────────────────
resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = "10.0.0.0/18"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.48.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.52.0.0/20"
  }
}

# ── Cluster GKE ───────────────────────────────────────────────────────────────
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region

  # Remover node pool padrão e criar separado (melhor prática)
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Segurança: habilitar Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Habilitar logging e monitoramento gerenciados
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
}

# ── Node Pool ─────────────────────────────────────────────────────────────────
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  autoscaling {
    min_node_count = 2
    max_node_count = 6
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = var.use_preemptible   # true em dev para economizar custos
    machine_type = var.machine_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      env     = var.environment
      project = var.cluster_name
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# ── Namespace via Terraform ───────────────────────────────────────────────────
resource "kubernetes_namespace" "loja_veloz" {
  metadata {
    name = "loja-veloz"
    labels = {
      "app.kubernetes.io/part-of"               = "loja-veloz"
      "pod-security.kubernetes.io/enforce"      = "restricted"
    }
  }

  depends_on = [google_container_cluster.primary]
}
