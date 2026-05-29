variable "project_id" {
  description = "ID do projeto no Google Cloud"
  type        = string
}

variable "region" {
  description = "Região GCP"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Nome do cluster GKE"
  type        = string
  default     = "loja-veloz-cluster"
}

variable "node_count" {
  description = "Número inicial de nodes"
  type        = number
  default     = 2
}

variable "machine_type" {
  description = "Tipo de máquina dos nodes"
  type        = string
  default     = "e2-standard-2"
}

variable "use_preemptible" {
  description = "Usar VMs preemptíveis (mais barato para dev)"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "prod"
}
