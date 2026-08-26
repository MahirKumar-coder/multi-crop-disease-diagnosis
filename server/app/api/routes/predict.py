from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status
from app.core.security import limiter
from app.services.preprocessor import validate_and_preprocess_image
from app.services.onnx_inference_service import onnx_service
from app.services.model_service import model_service
from app.services.gradcam_service import GradCAM
from app.services.cache_service import cache_service
from app.api.routes.diseases import disease_db
from app.schemas.prediction_schema import PredictionResponse, PredictionItem, RemediationPlan
from app.core.logger import logger

router = APIRouter()

# Target last convolutional block for PyTorch Grad-CAM explanation
target_conv_layer = model_service.model.features[-1]
grad_cam_engine = GradCAM(model_service.model, target_conv_layer)

@router.post("", response_model=PredictionResponse, summary="Analyze leaf image and get diagnosis with remedies")
@limiter.limit("30/minute")
async def predict_leaf_disease(request: Request, file: UploadFile = File(...)):
    # 1. Validate, Read bytes & Calculate SHA-256 Hash
    tensor, raw_image = await validate_and_preprocess_image(file)
    
    # Read raw bytes for deterministic hashing
    await file.seek(0)
    raw_bytes = await file.read()
    image_hash = cache_service.compute_image_hash(raw_bytes)

    # 2. Check Image Cache
    cached_result = cache_service.get(image_hash)
    if cached_result:
        cached_response = PredictionResponse(**cached_result)
        cached_response.cached = True
        return cached_response

    # 3. Execute Fast Multi-Threaded ONNX Inference
    try:
        top_class_id, top_confidence, raw_top3 = onnx_service.predict(raw_image)
    except Exception as e:
        logger.error(f"ONNX inference failed: {e}. Falling back to PyTorch model.")
        # Fallback to PyTorch
        tensor_dev = tensor.to(model_service.device)
        outputs = model_service.model(tensor_dev)
        import torch.nn.functional as F
        import torch
        probs = F.softmax(outputs, dim=1)[0]
        top3_prob, top3_indices = torch.topk(probs, 3)
        top_pred_idx = top3_indices[0].item()
        top_confidence = round(top3_prob[0].item() * 100, 2)
        top_class_id = model_service.class_names[top_pred_idx]
        raw_top3 = [
            {"class_id": model_service.class_names[idx.item()], "confidence": round(p.item() * 100, 2)}
            for p, idx in zip(top3_prob, top3_indices)
        ]

    # 4. Construct Top-3 Metadata List
    top_3_list = []
    for item in raw_top3:
        c_id = item["class_id"]
        c_meta = disease_db.get(c_id, {})
        top_3_list.append(
            PredictionItem(
                class_id=c_id,
                disease_name=c_meta.get("disease_name", c_id.replace("___", " - ")),
                crop=c_meta.get("crop", c_id.split("___")[0]),
                confidence=item["confidence"]
            )
        )

    # 5. Generate Grad-CAM Heatmap Overlay
    try:
        top_idx = model_service.class_names.index(top_class_id)
        tensor_grad = tensor.to(model_service.device)
        tensor_grad.requires_grad = True
        heatmap_base64 = grad_cam_engine.generate_heatmap(tensor_grad, top_idx, raw_image)
    except Exception as e:
        logger.warning(f"Grad-CAM generation failed: {e}")
        heatmap_base64 = None

    # 6. Retrieve Enriched Disease Knowledge
    meta = disease_db.get(top_class_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pathology data for class '{top_class_id}' not found in database."
        )

    response_data = PredictionResponse(
        predicted_class=top_class_id,
        crop=meta["crop"],
        disease_name=meta["disease_name"],
        scientific_name=meta.get("scientific_name", "N/A"),
        confidence=top_confidence,
        is_healthy=meta["is_healthy"],
        pathogen_type=meta["pathogen_type"],
        severity=meta["severity"],
        description=meta["description"],
        remediation=RemediationPlan(**meta["remediation"]),
        top_3_predictions=top_3_list,
        gradcam_heatmap_base64=heatmap_base64,
        cached=False,
        image_sha256=image_hash
    )

    # 7. Store in Cache
    cache_service.set(image_hash, response_data.model_dump())

    return response_data