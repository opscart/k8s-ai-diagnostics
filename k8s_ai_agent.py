import os
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from remediation import remediate_pod

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def namespace_exists(namespace):
    result = subprocess.run(
        ["kubectl", "get", "namespace", namespace],
        capture_output=True, text=True
    )
    return result.returncode == 0

def suggest_namespace(namespace):
    result = subprocess.run(["kubectl", "get", "ns", "-o", "json"], capture_output=True, text=True)
    ns_data = json.loads(result.stdout)
    all_namespaces = [ns["metadata"]["name"] for ns in ns_data["items"]]

    from difflib import get_close_matches
    suggestions = get_close_matches(namespace, all_namespaces, n=3)

    if suggestions:
        print(f"🔍 Did you mean: {', '.join(suggestions)}?")

def get_unhealthy_pods(namespace):
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
            capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            print(f"Error: Namespace '{namespace}' does not exist or cannot be accessed.")
            print(f"🔍 kubectl says: {result.stderr.strip()}")
            return None  # Signal an error

        data = json.loads(result.stdout)
        unhealthy_pods = []

        for pod in data["items"]:
            name = pod["metadata"]["name"]
            status = pod["status"].get("phase", "")
            container_statuses = pod["status"].get("containerStatuses", [])

            pod_unhealthy = False

            # Check basic pod status
            if status != "Running":
                pod_unhealthy = True

            for cs in container_statuses:
                # Check for waiting state with reason (e.g., CrashLoopBackOff, ImagePullBackOff, Unhealthy)
                waiting_state = cs.get("state", {}).get("waiting")
                if waiting_state and waiting_state.get("reason"):
                    pod_unhealthy = True
                    break
                
                # Check if container restarted too often
                if cs.get("restartCount", 0) > 3:
                    pod_unhealthy = True
                    break

                # Check if readiness probe failed (container not ready)
                if not cs.get("ready", True):
                    pod_unhealthy = True
                    break

                # Check if last termination was due to non-zero exit code
                last_terminated = cs.get("lastState", {}).get("terminated")
                if last_terminated and last_terminated.get("exitCode", 0) != 0:
                    pod_unhealthy = True
                    break

            if pod_unhealthy:
                unhealthy_pods.append(name)

        return unhealthy_pods

    except Exception as e:
        print(f"Unexpected error while checking pods: {e}")
        return None

def get_pod_info(pod_name, namespace):
    describe = subprocess.run(["kubectl", "describe", "pod", pod_name, "-n", namespace],
                              capture_output=True, text=True)
    logs = subprocess.run(["kubectl", "logs", pod_name, "-n", namespace],
                          capture_output=True, text=True)

    logs_output = logs.stdout if logs.returncode == 0 else "No logs available."
    return describe.stdout, logs_output

def analyze_with_gpt(pod_name, namespace, describe, logs):
    print(f"\n🤖 Analyzing pod: {pod_name}...\n")
    prompt = f"""You are a Kubernetes expert. Diagnose the following pod issue.

Namespace: {namespace}
Pod Name: {pod_name}

--- kubectl describe pod ---
{describe}

--- kubectl logs ---
{logs}

Please provide:
1. Root cause
2. Possible reasons
3. Suggested fixes
4. Any supporting evidence from logs/events
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Kubernetes SRE expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def main():
    namespace = input("Enter the namespace to scan: ").strip()

    if not namespace_exists(namespace):
        print(f"Error: Namespace '{namespace}' does not exist.")
        suggest_namespace(namespace)  # Optional
        return

    unhealthy_pods = get_unhealthy_pods(namespace)
    if unhealthy_pods is None:
        return

    if not unhealthy_pods:
        print("All pods are healthy in this namespace.")
        return

    print(f"🔍 Found {len(unhealthy_pods)} unhealthy pod(s): {unhealthy_pods}")

    for pod in unhealthy_pods:
        describe, logs = get_pod_info(pod, namespace)
        result = analyze_with_gpt(pod, namespace, describe, logs)

        print(f"\nDiagnosis for pod {pod}:\n{result}")
        print("=" * 80)
        # 🔧 Dry-run remediation
        from remediation import remediate_pod
        remediate_pod(pod, namespace, result, dry_run=True)

if __name__ == "__main__":
    main()

