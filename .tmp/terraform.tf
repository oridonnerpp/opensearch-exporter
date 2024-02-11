resource "aws_iam_role" "mantis_system_opensearch_exporter_role" {
  name = "mantis-system-opensearch-exporter-${var.logical_env_name}"

  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json

  inline_policy {
    name = "mantis-system-opensearch-exporter-read-only"

    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "es:ESHttpGet",
            "es:ESHttpHead",
            "es:ESHttpGet",
            "es:ESHttpHead"
          ]
          Resource = [
            "arn:aws:es:us-east-*:${var.aws_account_id}:domain/logs*",
            "arn:aws:es:us-east-*:${var.aws_account_id}:domain/logs*/*"
          ]
        }
      ]
    })
  }
}
