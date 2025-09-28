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
  - Offers a dry-run mode for human approval before remediation  
  - Logs all actions with timestamps and command results  
  - Uses minimal dependencies (just `kubectl`, OpenAI API, and Python)

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

### Execution
```bash
$ python3 k8s_ai_agent.py
Enter the namespace to scan: ai-apps
🔍 Found 4 unhealthy pod(s): ['broken-nginx', 'oom-test', 'crashy', 'unhealthy-probe']

🤖 Analyzing pod: crashy...
🔧 Detected CrashLoopBackOff. Suggest restarting the pod.
🤖 Do you want to apply the above remediation? (yes/no): yes
✅ Deployment crashy is now healthy.

🤖 Analyzing pod: oom-test...
🔧 Detected OOMKilled. Suggest increasing memory limits.
🤖 Do you want to apply the above remediation? (yes/no): yes
✅ Deployment oom-test is now healthy.

🤖 Analyzing pod: broken-nginx...
🔧 ImagePullBackOff detected — likely an image issue.
🟡 Skipping remediation.

🤖 Analyzing pod: unhealthy-probe...
🔧 Probe failure detected — likely due to missing files.
🟡 Skipping remediation.
```

## Remediation Types & Strategies
**Issue	Diagnosis Type	Action Takßen**
- ImagePullBackOff	Image issue	Skipped with manual comment/reminder
- CrashLoopBackOff	Container crash	Pod restarted (via kubectl delete pod)
- OOMKilled	Memory overuse	Deployment memory limit patched (to 400Mi) [actual mem size shoud taken from usage pattern]
- Probe failure	Misconfigured probes	Manual remediation suggested (no patch)

## Current Limitations

- No remediation for custom probe logic (manual step recommended)
- Assumes single-container deployments for memory patching
- Only the first container in pod is considered for resource checks
- Currently CLI-interactive (no web UI yet)
