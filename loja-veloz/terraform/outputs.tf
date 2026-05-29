output "cluster_name" {
  description = "Nome do cluster GKE"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "Endpoint do cluster"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "kubectl_config_command" {
  description = "Comando para configurar kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}
