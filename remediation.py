import subprocess
import datetime
import traceback

def remediate_pod(pod_name, namespace, diagnosis, dry_run=True):
    actions = []
    remediation_type = None

    def infer_deployment_name(pod_name):
        # Assumes pod name is like: <deployment-name>-<replicaSet-hash>-<random>
        return "-".join(pod_name.split("-")[:-2])
    deployment_name = infer_deployment_name(pod_name)
    if "OOMKilled" in diagnosis:
        remediation_type = "memory_patch"
        print(f"🔧 Detected OOMKilled. Suggest increasing memory limits.")

        recommended_mem = "400Mi"
        deployment_name = infer_deployment_name(pod_name)

        patch_cmd = (
            f"kubectl patch deployment {deployment_name} -n {namespace} --type='json' "
            f"-p='[{{\"op\": \"replace\", \"path\": \"/spec/template/spec/containers/0/resources/limits/memory\", "
            f"\"value\": \"{recommended_mem}\"}}]'"
        )

        print(f"💡 Dry run: Would patch deployment memory limit to {recommended_mem}")
        print(f"🔍 Patch command: {patch_cmd}")
        actions.append(patch_cmd)
        verify_cmd = f"kubectl get deployment {deployment_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.limits.memory}}'"
        res = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
        print(f"📦 Verified memory limit: {res.stdout.strip()}")

    elif "CrashLoopBackOff" in diagnosis:
        print(f"🔧 Detected CrashLoopBackOff. Suggest restarting the pod.")

        restart_cmd = f"kubectl delete pod {pod_name} -n {namespace}"
        remediation_type = "restart_pod"
        print(f"💡 Dry run: Would restart pod {pod_name}")
        print(f"🔍 Restart command: {restart_cmd}")
        actions.append(restart_cmd)

    elif "probe" in diagnosis.lower() or "Liveness probe failed" in diagnosis:
        print(f"🔧 Detected probe failure. You may need to patch or remove the liveness/readiness probe.")
        remediation_type = "manual_probe_fix"  # ← Add this line here
        patch_cmd = f"# You might want to patch the probe config for pod {pod_name}"
        print(f"💡 Dry run: Probe-related remediation would be required.")
        print(f"🔍 Suggest editing the deployment manually or update YAML.")
        actions.append(patch_cmd)


    elif "ImagePullBackOff" in diagnosis:
        print(f"🔧 ImagePullBackOff detected — likely an image issue.")
        print(f"💡 Please check the image name or pull secrets. No safe automated remediation.")
        actions.append("# Manual remediation recommended for image issues.")

    else:
        print("⚠️ No automatic remediation available.")
        return

    # 🔽 This part was missing — it prompts the user and applies remediation
    if dry_run:
        confirm = input("🤖 Do you want to apply the above remediation? (yes/no): ").strip().lower()
        if confirm == "yes":
            for cmd in actions:
                if cmd.startswith("#"):
                    print(f"⚠️ Skipping comment/reminder: {cmd}")
                    continue
                run_and_log(cmd)

            # ✅ Only verify deployment health if actual action was taken
            if remediation_type in ["memory_patch", "restart_pod"]:
                print("🔍 Verifying deployment health...")
                wait_cmd = (
                    f"kubectl wait --for=condition=Available deployment/{deployment_name} "
                    f"-n {namespace} --timeout=30s"
                )
                wait_result = subprocess.run(wait_cmd, shell=True, capture_output=True, text=True)

                verification_msg = (
                    f"✅ Deployment {deployment_name} is now healthy."
                    if wait_result.returncode == 0
                    else f"❌ Deployment {deployment_name} is still not healthy.\n🔴 {wait_result.stderr.strip()}"
                )
                print(verification_msg)

        if remediation_type in ["memory_patch", "restart_pod"]:
            # ✅ Log verification result (Change 3)
            with open("remediation.log", "a") as log_file:
                log_file.write(
                    f"{datetime.datetime.now()} | {wait_cmd} | "
                    f"ReturnCode: {wait_result.returncode} | "
                    f"Output: {wait_result.stdout.strip()} | "
                    f"Error: {wait_result.stderr.strip()}\n"
                )
        else:
            print("🟡 Skipping remediation.")
    else:
        for cmd in actions:
            if not cmd.startswith("#"):
                run_and_log(cmd)


def run_and_log(cmd):
    try:
        print(f"🔧 Executing: {cmd}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        with open("remediation.log", "a") as log_file:
            log_entry = (
                f"{datetime.datetime.now()} | {cmd} | "
                f"ReturnCode: {res.returncode} | "
                f"Output: {res.stdout.strip()} | "
                f"Error: {res.stderr.strip()}\n"
            )
            log_file.write(log_entry)

        if res.returncode != 0:
            print(f"❌ Command failed with return code {res.returncode}")
            print(f"🔴 STDERR: {res.stderr.strip()}")

    except Exception:
        print("🔥 Exception occurred while executing remediation command:")
        traceback.print_exc()
