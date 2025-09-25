import subprocess
import datetime

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error running '{cmd}': {result.stderr.strip()}")
    else:
        print(f"✅ Success: {result.stdout.strip()}")
    return result

def remediate_pod(pod_name, namespace, diagnosis):
    # Map diagnosis root cause keywords to remediation commands
    actions = []

    if "unable to pull the Docker image" in diagnosis or "ImagePullBackOff" in diagnosis:
        # Example: update image or notify user to fix YAML
        fix_image = input(f"Pod '{pod_name}' has image pull issue. Do you want to update image to 'nginx:latest'? (y/n): ")
        if fix_image.lower() == 'y':
            actions.append(f"kubectl set image pod/{pod_name} nginx=nginx:latest -n {namespace}")

    elif "CrashLoopBackOff" in diagnosis or "continuously crashing" in diagnosis:
        restart_pod = input(f"Pod '{pod_name}' is crashing. Do you want to delete the pod to restart it? (y/n): ")
        if restart_pod.lower() == 'y':
            actions.append(f"kubectl delete pod {pod_name} -n {namespace}")

    if not actions:
        print("No remediation actions defined for this diagnosis or no actions selected.")
        return

    # Execute actions and log results
    with open("remediation.log", "a") as log_file:
        for cmd in actions:
            print(f"Running remediation command: {cmd}")
            res = run_command(cmd)
            log_entry = f"{datetime.datetime.now()} | {cmd} | ReturnCode: {res.returncode} | Output: {res.stdout.strip()} | Error: {res.stderr.strip()}\n"
            log_file.write(log_entry)

