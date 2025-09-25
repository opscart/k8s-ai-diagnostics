# Kubernetes AI Agent

This project is an AI-powered Kubernetes troubleshooting assistant that:

- Detects unhealthy pods in a given namespace
- Diagnoses pod issues using OpenAI GPT-4 by analyzing pod descriptions and logs
- Provides detailed root cause analysis and suggested fixes for common pod failures
- Planned: Automates remediation actions based on diagnosis

---

## Features So Far

- **Namespace validation**: Verifies if the namespace exists before scanning pods.
- **Unhealthy pod detection**: Detects pods in statuses such as `CrashLoopBackOff`, `ImagePullBackOff`, `OOMKilled`, and failing health probes.
- **Detailed diagnosis**: Uses OpenAI GPT-4 to analyze pod descriptions and logs, providing:
  - Root cause analysis
  - Possible reasons
  - Suggested fixes
  - Supporting evidence from events and logs
- **Multiple failure scenarios covered**:
  - Image pull errors
  - Crash loop errors
  - Out-of-memory kills
  - Readiness/liveness probe failures

---

## Getting Started

### Prerequisites

- Python 3.8+
- Access to a Kubernetes cluster with `kubectl` configured
- An OpenAI API key (stored in `.env` as `OPENAI_API_KEY`)

### Installation

```bash
git clone <repo-url>
cd ai-agent-poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

