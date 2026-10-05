terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws     = { source = "hashicorp/aws", version = "~> 5.60" }
    datadog = { source = "DataDog/datadog", version = "~> 3.45" }
  }
}

variable "alarm_topic_arn" {
  type        = string
  description = "SNS topic para notificaciones"
}

variable "bucket_name" {
  type = string
}

# --- CloudWatch: deteccion de acceso denegado y cambios de politica (PCI 10.4 / 10.7) ---
resource "aws_cloudwatch_metric_alarm" "s3_4xx" {
  alarm_name          = "${var.bucket_name}-4xx-errors"
  namespace           = "AWS/S3"
  metric_name         = "4xxErrors"
  dimensions          = { BucketName = var.bucket_name, FilterId = "EntireBucket" }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 50
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alarm_topic_arn]
  alarm_description   = "Posible enumeracion/intento de acceso no autorizado"
}

# --- Datadog: monitor de ejemplo (requiere API/APP keys por variables de entorno) ---
resource "datadog_monitor" "keycloak_availability" {
  name    = "Keycloak - pods no disponibles"
  type    = "metric alert"
  message = "Keycloak con menos de 1 replica disponible. @slack-platform-alerts"
  query   = "min(last_5m):avg:kubernetes_state.deployment.replicas_available{kube_deployment:keycloak} < 1"

  monitor_thresholds {
    critical = 1
  }
  tags = ["service:keycloak", "team:platform"]
}
