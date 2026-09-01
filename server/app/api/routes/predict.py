import hashlib
from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException, status
from app.services.preprocessor import validate_and_preprocess_image
from app.services.onnx_inference_service import onnx_service
from app.services.gradcam_service import gradcam_service
from app.services.knowledge_base_service import kb_service
from app.schemas.prediction import PredictionResponse, PredictionItem
from app.core.security import limiter
from app.core.logger import logger

router = APIRouter()

# In-memory SHA-256 caching table
_INFERENCE_CACHE = {}

@router.post("", response_model=PredictionResponse)
@router.post("/", response_model=PredictionResponse)
@limiter.limit("30/minute")
async def predict_crop_disease(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Analyzes leaf images with:
    - Magic-byte & decompression bounds validation
    - In-memory SHA-256 response caching
    - Temperature-calibrated ONNX inference
    - Out-of-distribution (OOD) ambiguous scan warning (<60% confidence)
    - Grad-CAM explainability and remediation metadata retrieval
    """
    # 1. Read buffer for SHA-256 Cache Check
    contents = await file.read()
    await file.seek(0)
    image_hash = hashlib.sha256(contents).hexdigest()

    if image_hash in _INFERENCE_CACHE:
        cached_res = _INFERENCE_CACHE[image_hash].copy()
        cached_res["cached"] = True
        return cached_res

    # 2. Validate and Preprocess Image
    tensor, raw_image = await validate_and_preprocess_image(file)

    # 3. Run Calibrated ONNX Inference
    diag_result = onnx_service.predict(tensor)
    
    primary_pred = diag_result["primary_prediction"]
    top_3_raw = diag_result["top_k_predictions"]
    predicted_class_name = primary_pred["class_name"]

    # 4. Parse Crop & Disease Name from Class Identifier
    if "___" in predicted_class_name:
        crop_name, disease_clean = predicted_class_name.split("___", 1)
        crop_name = crop_name.replace("_", " ").title()
        disease_clean = disease_clean.replace("_", " ").title()
    else:
        crop_name = "Unknown"
        disease_clean = predicted_class_name

    is_healthy = "healthy" in predicted_class_name.lower()

    # 5. Lookup Remediation Knowledge Base
    kb_record = kb_service.get_disease_details(predicted_class_name)
    
    # 6. Generate Grad-CAM Heatmap Overlay
    heatmap_base64 = None
    try:
        heatmap_base64 = gradcam_service.generate_base64_heatmap(tensor, primary_pred["class_id"], raw_image)
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {str(e)}")

    # 7. Assemble Structured Response
    top_3_formatted = [
        PredictionItem(
            class_id=item["class_id"],
            class_name=item["class_name"],
            confidence=item["confidence"]
        )
        for item in top_3_raw
    ]

    response_payload = {
        "predicted_class": predicted_class_name,
        "crop": crop_name,
        "disease_name": disease_clean,
        "confidence": primary_pred["confidence"],
        "is_healthy": is_healthy,
        "pathogen_type": kb_record.get("pathogen_type") if kb_record else None,
        "severity": kb_record.get("severity") if kb_record else None,
        "description": kb_record.get("description") if kb_record else None,
        "is_confident": diag_result["is_confident"],
        "status_flag": diag_result["status_flag"],
        "warning_message": diag_result["warning_message"],
        "top_3_predictions": top_3_formatted,
        "remediation": kb_record.get("remediation") if kb_record else None,
        "gradcam_heatmap_base64": heatmap_base64,
        "inference_time_ms": diag_result["inference_time_ms"],
        "cached": False
    }

    # Store in memory cache
    _INFERENCE_CACHE[image_hash] = response_payload

    return response_payload