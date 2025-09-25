import os
import subprocess
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

def get_pod_description(pod_name: str, namespace: str = "default") -> str:
    try:
        result = subprocess.run(
            ["kubectl", "describe", "pod", pod_name, "-n", namespace],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("❌ Failed to describe pod:", e)
        return ""

def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    try:
        result = subprocess.run(
            ["kubectl", "logs", pod_name, "-n", namespace],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("❌ Failed to get logs for pod:", e)
        return "No logs available or logs failed to retrieve."

def analyze_with_gpt(pod_description: str, pod_logs: str) -> str:
    prompt = f"""
You are a Kubernetes expert. Analyze the following Kubernetes pod diagnostics and help identify the issue.

1. Provide a root cause analysis (RCA)
2. List possible reasons
3. Suggest specific fixes
4. Mention any logs or events that support your diagnosis

--- POD DESCRIPTION ---
{pod_description}

--- POD LOGS ---
{pod_logs}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a DevOps AI agent helping debug Kubernetes pods."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    pod_name = input("Enter the pod name (e.g. broken-nginx): ")
    namespace = input("Namespace [default]: ") or "default"
    
    print("\n🔍 Fetching pod description...")
    pod_desc = get_pod_description(pod_name, namespace)

    print("📜 Fetching pod logs...")
    pod_logs = get_pod_logs(pod_name, namespace)

    print("\n🤖 Sending to AI agent...")
    result = analyze_with_gpt(pod_desc, pod_logs)

    print("\n💡 AI Diagnosis:\n")
    print(result)

