import os
import torch
from network import PlantDiseaseClassifier

def export_onnx_pipeline(
    weights_path: str,
    output_path: str = "../models/efficientnet_plant_disease.onnx",
    num_classes: int = 38
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    model = PlantDiseaseClassifier(num_classes=num_classes)
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=False)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )
    print(f"Exported production ONNX model to: {output_path}")

if __name__ == "__main__":
    export_onnx_pipeline("../models/checkpoints/best_efficientnet.pt")