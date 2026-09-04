import os
import json
import hashlib
from datetime import datetime, timezone

ARTIFACT_PATHS = {
    "pytorch_checkpoint": "../models/checkpoints/best_efficientnet_v2.pt",
    "quantized_onnx_engine": "../models/exported/efficientnet_b0_quantized.onnx",
    "production_backend_model": "../../app/models/efficientnet_plant_disease.onnx",
    "class_indices": "../data/class_indices.json",
    "calibration_config": "../models/calibration_config.json"
}

MANIFEST_OUT = "../models/model_manifest.json"

def compute_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest():
    print("=" * 70)
    print(" 🛡️ FREEZING MODEL ARTIFACTS & GENERATING CHECKSUM MANIFEST")
    print("=" * 70)

    manifest = {
        "project": "Multi-Crop Plant Disease Detection and Remediation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "architecture": "EfficientNet-B0 (Dynamic INT8 Quantized)",
        "frameworks": ["PyTorch 2.2", "ONNX Runtime 1.17", "Albumentations 1.4"],
        "artifacts": {}
    }

    for name, rel_path in ARTIFACT_PATHS.items():
        full_path = os.path.normpath(os.path.join(os.path.dirname(__file__), rel_path))
        if os.path.exists(full_path):
            size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 3)
            checksum = compute_sha256(full_path)
            manifest["artifacts"][name] = {
                "path": rel_path,
                "size_mb": size_mb,
                "sha256": checksum,
                "status": "VERIFIED"
            }
            print(f"[{name.upper()}]")
            print(f"  --> Path   : {rel_path}")
            print(f"  --> Size   : {size_mb} MB")
            print(f"  --> SHA-256: {checksum}\n")
        else:
            manifest["artifacts"][name] = {
                "path": rel_path,
                "status": "MISSING"
            }
            print(f"⚠️ Warning: Missing artifact at {full_path}\n")

    os.makedirs(os.path.dirname(os.path.abspath(MANIFEST_OUT)), exist_ok=True)
    with open(MANIFEST_OUT, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Checkpoint manifest locked and saved to: {MANIFEST_OUT}")

if __name__ == "__main__":
    generate_manifest()