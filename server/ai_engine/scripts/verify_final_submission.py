import os
import json
import hashlib
from typing import Dict, Any

MANIFEST_PATH = "../models/model_manifest.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def audit_and_freeze_ai_engine():
    print("=" * 75)
    print(" 🧊 AI ENGINE FINAL VERIFICATION & SUBMISSION AUDIT")
    print("=" * 75)

    manifest_full_path = os.path.normpath(os.path.join(BASE_DIR, MANIFEST_PATH))
    if not os.path.exists(manifest_full_path):
        raise FileNotFoundError(f"Manifest missing: {manifest_full_path}")

    with open(manifest_full_path, "r") as f:
        manifest_data = json.load(f)

    all_passed = True

    # 1. Verify Weights and Artifact Signatures
    print("\n[Phase 1/3: Validating Cryptographic Artifact Checksums]")
    for key, item in manifest_data["artifacts"].items():
        rel_path = item["path"]
        expected_hash = item["sha256"]
        target_path = os.path.normpath(os.path.join(BASE_DIR, "../models", rel_path))

        if not os.path.exists(target_path):
            print(f"  ❌ FAILED: File missing -> {rel_path}")
            all_passed = False
            continue

        actual_hash = compute_sha256(target_path)
        actual_size_mb = os.path.getsize(target_path) / (1024 * 1024)

        if actual_hash == expected_hash:
            print(f"  ✅ VERIFIED: {key} ({actual_size_mb:.2f} MB)")
            print(f"     SHA-256: {actual_hash[:32]}...")
        else:
            print(f"  ❌ CHECKSUM MISMATCH: {key}")
            print(f"     Expected: {expected_hash}")
            print(f"     Actual  : {actual_hash}")
            all_passed = False

    # 2. Audit Colab Notebook Cleanliness
    print("\n[Phase 2/3: Sanitizing Colab Training Notebooks]")
    notebook_dir = os.path.normpath(os.path.join(BASE_DIR, "../../notebooks"))
    notebooks = [f for f in os.listdir(notebook_dir) if f.endswith(".ipynb")] if os.path.exists(notebook_dir) else []
    
    if not notebooks:
        print("  ⚠️ Warning: No local notebooks found in server/notebooks/. Ensure Colab link is live.")
    else:
        for nb in notebooks:
            nb_path = os.path.join(notebook_dir, nb)
            with open(nb_path, "r", encoding="utf-8") as nf:
                content = nf.read()
                # Check for exposed API tokens or sensitive credentials
                sensitive_keys = ["ghp_", "sk-", "render_api_", "aws_access_key"]
                leak_found = any(k in content for k in sensitive_keys)
                if leak_found:
                    print(f"  🚨 SECURITY ALERT: Sensitive tokens detected in {nb}!")
                    all_passed = False
                else:
                    print(f"  ✅ SANITIZED: {nb} (No plain-text API secrets detected)")

    # 3. Print Final Sign-off Status
    print("\n[Phase 3/3: AI Module Freeze Status]")
    if all_passed:
        print("  🎉 STATUS: AI ENGINE FROZEN & READY FOR VIVA DEFENSE")
    else:
        print("  ⚠️ STATUS: AUDIT FAILED. Resolve highlighted issues before submission.")
    print("=" * 75)

if __name__ == "__main__":
    audit_and_freeze_ai_engine()