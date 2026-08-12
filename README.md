# AI FinOps Platform

AI-powered AWS cost anomaly detection and automated remediation.

## Tech Stack
| Layer | Tool |
|---|---|
| Infrastructure | Terraform |
| Compute | AWS Lambda (Python 3.11) |
| Data | AWS Cost Explorer + CloudWatch |
| AI | AWS Bedrock (Claude 3 Haiku) |
| Alerts | Slack Webhooks |
| Dashboards | Grafana (Docker) |
| CI/CD | GitHub Actions |
| Security | Checkov + Trivy |
| Storage | SQLite |

## Project Status
- [x] Phase 0 - Repo, Terraform, IAM, Docker, CI skeleton
- [ ] Phase 1 - Data collection
- [ ] Phase 2 - Anomaly detection
- [ ] Phase 3 - AI RCA (Bedrock)
- [ ] Phase 4 - Slack alerts + CI/CD
- [ ] Phase 5 - Grafana dashboards
- [ ] Phase 6 - Security scanning
- [ ] Phase 7 - Documentation
