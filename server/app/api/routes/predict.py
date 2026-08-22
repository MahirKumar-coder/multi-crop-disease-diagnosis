import torch
import torch.nn.functional as F
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.preprocessor import validate_and_preprocess_image
from app.services.model_service import model_service
from app.services.gradcam_service import GradCAM
from app.api.routes.diseases import disease_db
from app.schemas.prediction_schema import PredectionResponse, PredictionItem, RemediationPlan
from app.core.logger import logger

router = APIRouter()

target_conv_layer = model_service.model.features[-1]
grad_cam_engine = GradCAM(model_service.model, target_conv_layer)

@router.post("", response_model=PredectionResponse, summary="Analyze leaf image and get diagnosis with remedies")
async def predict_leaf_disease(file: UploadFile = File(...)):

    tensor, raw_image = await validate_and_preprocess_image(file)
    tensor = tensor.to(model_service.device)

    tensor.requires_grad = True
    outputs = model_service.model(tensor)
    probabilities = F.softmax(outputs, dim=1)[0]

    top3_prob, top3_indices = torch.topk(probabilities, 3)
    top_pred_idx = top3_indices[0].item()
    top_confidence = top3_prob[0].item()
    top_class_id = model_service.class_names[top_pred_idx]

    top_3_list = []
    for p, idx in zip(top3_prob, top3_indices):
        c_id = model_service.class_names[idx.item()]
        c_meta = disease_db.get(c_id, {})
        top_3_list.append(
            PredictionItem(
                class_id=c_id,
                disease_name=c_meta.get("disease_name", c_id.replace("___", " - ")),
                crop=c_meta.get("crop", c_id.split("___")[0]),
                confidence=round(p.item() * 100, 2)
            )
        )

        try:
            heatmap_base64 = grad_cam_engine.generate_heatmap(tensor, top_pred_idx, raw_image)
        except Exception as e: 
            logger.warning(f"Grad-CAM generation failed: {e}")
            heatmap_base64 = None

        meta = disease_db.get(top_class_id, {
            "crop": top_class_id.split("___")[0],
            "disease_name": top_class_id.replace("___", " - "),
            "is_healthy": "healthy" in top_class_id.lower(),
            "pathogen_type": "Unknown",
            "severity": "Medium",
            "description": "Pathology details unavailable.",
            "remediation": {
                "organic": ["Maintain proper aeration and sunlight."],
                "chemical": ["Consult local agricultural extension center."],
                "preventive": ["Prune damaged area and practice crop rotation."]
            }
        })

        return PredectionResponse(
            predicted_class=top_class_id,
            crop=meta["crop"],
            disease_name=meta["disease_name"],
            confidence=round(top_confidence * 100, 2),
            is_healthy=meta["is_healthy"],
            pathogen_type=meta["pathogen_type"],
            severity=meta["severity"],
            description=meta["description"],
            remediation=RemediationPlan(**meta["remediation"]),
            top_3_predictions=top_3_list,
            gradcam_heatmap_base64=heatmap_base64
        )