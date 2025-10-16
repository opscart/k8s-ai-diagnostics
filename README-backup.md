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
```

## Environment Setup & Local Deployment

Follow these steps to deploy the AI diagnostics scenarios locally.

---

### 1. Clone the Repository

```bash
git clone https://github.com/opscart/k8s-ai-diagnostics.git
cd k8s-ai-diagnostics
```

### 2. Create & Activate Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now look like:

```bash
(venv) opscart@U00098 first-ai-agent %
```

#### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Kubernetes Namespace

Make sure you have a local Kubernetes cluster running (e.g., minikube or kind). Create the namespace:

```bash
kubectl create namespace ai-apps
```

### 5. Deploy the AI Diagnostics Scenarios

Run the deployment script:

```bash
sh k8s-manifests/deploy.sh
```

You should see output similar to:

```bash
Deleting existing deployments...
deployment.apps "broken-nginx" deleted from ai-apps namespace
deployment.apps "crashy" deleted from ai-apps namespace
deployment.apps "unhealthy-probe" deleted from ai-apps namespace
deployment.apps "oom-test" deleted from ai-apps namespace
Applying deployments...
deployment.apps/broken-nginx created
deployment.apps/crashy created
deployment.apps/unhealthy-probe created
deployment.apps/oom-test created
Done.
```
Running script to deploy:

```bash
$ python3 k8s_ai_agent.py
Enter the namespace to scan: ai-apps
Found 4 unhealthy pod(s): ['broken-nginx', 'oom-test', 'crashy', 'unhealthy-probe']

Analyzing pod: crashy...
Detected CrashLoopBackOff. Suggest restarting the pod.
Do you want to apply the above remediation? (yes/no): yes
Deployment crashy is now healthy.

Analyzing pod: oom-test...
Detected OOMKilled. Suggest increasing memory limits.
Do you want to apply the above remediation? (yes/no): yes
Deployment oom-test is now healthy.

Analyzing pod: broken-nginx...
ImagePullBackOff detected — likely an image issue.
Skipping remediation.

Analyzing pod: unhealthy-probe...
Probe failure detected — likely due to missing files.
Skipping remediation.
```

### 6. Verify Deployment

Check deployments:
```bash
kubectl get deployment -n ai-apps


Check pods:

kubectl get pod -n ai-apps


Expected pod statuses:

NAME                               READY   STATUS             RESTARTS      AGE
broken-nginx-5f6cdfb774-m7kw7      0/1     ImagePullBackOff   0             7m
crashy-77747bbb47-mr75j            0/1     CrashLoopBackOff   6             7m
oom-test-5fd8f6b8d9-c9p52          1/1     Running            0             2m
unhealthy-probe-78d9b76567-5x8h6   0/1     Running            1             1m
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
