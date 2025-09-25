import subprocess
import datetime
import json

def run_command(cmd):
    """Run a shell command and return CompletedProcess object."""
    return subprocess.run(cmd, capture_output=True, text=True)

def get_current_memory_limit(pod_name, namespace):
    """
    Retrieve current memory limit of the first container in the pod.
    Returns memory string like '200Mi' or None if not found.
    """
    cmd = ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"]
    result = run_command(cmd)
    if result.returncode != 0:
        print(f"Error fetching pod info: {result.stderr.strip()}")
        return None
    try:
        pod_data = json.loads(result.stdout)
        containers = pod_data["spec"]["containers"]
        if containers:
            resources = containers[0].get("resources", {})
            limits = resources.get("limits", {})
            mem_limit = limits.get("memory")
            return mem_limit
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing pod JSON: {e}")
    return None

def increase_memory(mem_str, factor=1.5):
    """
    Increase memory limit by a factor.
    Supports 'Mi' or 'Gi' suffixes.
    """
    if not mem_str:
        return None

    units = {"Mi": 1, "Gi": 1024}
    for unit in units:
        if mem_str.endswith(unit):
            try:
                val = float(mem_str[:-len(unit)])
                new_val = int(val * factor)
                # Return with same unit
                return f"{new_val}{unit}"
            except ValueError:
                return None
    # Unknown format, just return None
    return None

def generate_patch_memory_cmd(pod_name, namespace, new_memory_limit):
    """
    Generate kubectl patch command to update memory limit of first container.
    """
    patch = {
        "spec": {
            "containers": [{
                "name": pod_name,  # Assumes container name == pod name; adjust if needed
                "resources": {
                    "limits": {"memory": new_memory_limit}
                }
            }]
        }
    }
    patch_str = json.dumps(patch)
    cmd = [
        "kubectl", "patch", "pod", pod_name, "-n", namespace,
        "--type=merge",
        f"--patch={patch_str}"
    ]
    return cmd

def ask_user_to_confirm(cmd):
    """
    Prompt user to confirm remediation action.
    """
    print(f"Proposed command:\n{' '.join(cmd)}")
    resp = input("Apply this remediation? (y/N): ").strip().lower()
    return resp == 'y'

def apply_patch(cmd):
    """
    Apply patch by running the kubectl command.
    """
    result = run_command(cmd)
    if result.returncode == 0:
        print("Patch applied successfully.")
    else:
        print(f"Failed to apply patch: {result.stderr.strip()}")
    log_remediation_action(" ".join(cmd), result)
    return result

def restart_pod(pod_name, namespace):
    """
    Delete pod to trigger restart.
    """
    cmd = ["kubectl", "delete", "pod", pod_name, "-n", namespace]
    result = run_command(cmd)
    if result.returncode == 0:
        print(f"Pod {pod_name} restarted successfully.")
    else:
        print(f"Failed to restart pod {pod_name}: {result.stderr.strip()}")
    log_remediation_action(" ".join(cmd), result)
    return result

def log_remediation_action(cmd, result):
    """
    Log remediation command execution to remediation.log.
    """
    with open("remediation.log", "a") as log_file:
        log_entry = (
            f"{datetime.datetime.now()} | {cmd} | "
            f"ReturnCode: {result.returncode} | "
            f"Output: {result.stdout.strip()} | "
            f"Error: {result.stderr.strip()}\n"
        )
        log_file.write(log_entry)

def parse_remediation_log(log_path="remediation.log"):
    """
    Parse remediation.log into list of dict entries.
    """
    history = []
    try:
        with open(log_path, "r") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 4:
                    try:
                        entry = {
                            "timestamp": parts[0],
                            "command": parts[1],
                            "returncode": int(parts[2].split(": ")[1]),
                            "output": parts[3].split(": ", 1)[1] if len(parts[3].split(": ")) > 1 else "",
                            "error": parts[4].split(": ", 1)[1] if len(parts) > 4 else "",
                        }
                        history.append(entry)
                    except Exception:
                        continue
    except FileNotFoundError:
        pass  # No log yet
    return history

def was_remediation_successful(command, history):
    """
    Check if a remediation command was previously run successfully.
    """
    for entry in reversed(history):
        if entry["command"] == command:
            return entry["returncode"] == 0
    return False

def remediate_pod(pod_name, namespace, diagnosis, dry_run=True):
    """
    Decide remediation action based on diagnosis and pod info.
    If dry_run, prepare the action but do not apply.
    """
    history = parse_remediation_log()
    
    if "OOMKilled" in diagnosis:
        current_mem = get_current_memory_limit(pod_name, namespace)
        if not current_mem:
            print("Could not retrieve current memory limit. Skipping remediation.")
            return
        
        recommended_mem = increase_memory(current_mem, factor=1.5)
        if not recommended_mem:
            print("Could not calculate recommended memory. Skipping remediation.")
            return

        patch_cmd = generate_patch_memory_cmd(pod_name, namespace, recommended_mem)
        cmd_str = " ".join(patch_cmd)

        if was_remediation_successful(cmd_str, history):
            print(f"Remediation already applied successfully: {cmd_str}")
            return

        if dry_run:
            print(f"Dry run: Would patch memory limits from {current_mem} to {recommended_mem}")
            if ask_user_to_confirm(patch_cmd):
                apply_patch(patch_cmd)
        else:
            apply_patch(patch_cmd)

    elif "CrashLoopBackOff" in diagnosis:
        restart_cmd = f"kubectl delete pod {pod_name} -n {namespace}"
        if was_remediation_successful(restart_cmd, history):
            print(f"Restart already performed successfully: {restart_cmd}")
            return
        
        print(f"Dry run: Would restart pod {pod_name}")
        if not dry_run:
            restart_pod(pod_name, namespace)

    elif "Probe failure" in diagnosis or "Unhealthy" in diagnosis:
        # Placeholder for probe remediation logic
        print(f"Probe failure detected for pod {pod_name}.")
        print("Dry run: Would patch probe configuration (not implemented).")
        # Could implement patching readiness/liveness probes here
        # Ask user confirmation, generate patch, apply_patch() etc.

    else:
        print("No automatic remediation available. Please check manually.")

