import os
import time
import torch
import numpy as np
from PIL import Image
import torchvision.models as models
import onnxruntime as ort

def generate_dummy_onnx(onnx_path="test_model.onnx"):
    print("Generating baseline model and exporting ONNX...")
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 38)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input"],
        output_names=["output"],
        opset_version=18
    )
    return model

def benchmark_inference(iterations=100):
    onnx_path = "test_model.onnx"
    torch_model = generate_dummy_onnx(onnx_path)

    # 1. PyTorch CPU Benchmark
    torch_input = torch.randn(1, 3, 224, 224)
    # Warmup
    for _ in range(10):
        _ = torch_model(torch_input)

    start_torch = time.perf_counter()
    with torch.no_grad():
        for _ in range(iterations):
            _ = torch_model(torch_input)
    torch_duration = (time.perf_counter() - start_torch) / iterations * 1000

    # 2. ONNX Runtime Multi-Threaded Benchmark
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = os.cpu_count() or 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(onnx_path, sess_options=opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    np_input = np.random.randn(1, 3, 224, 224).astype(np.float32)

    # Warmup
    for _ in range(10):
        _ = session.run(None, {input_name: np_input})

    start_onnx = time.perf_counter()
    for _ in range(iterations):
        _ = session.run(None, {input_name: np_input})
    onnx_duration = (time.perf_counter() - start_onnx) / iterations * 1000

    # Speedup calculation
    speedup = torch_duration / onnx_duration

    print("\n" + "="*50)
    print("      INFERENCE ENGINE BENCHMARK REPORT")
    print("="*50)
    print(f"Iterations Evaluated        : {iterations}")
    print(f"PyTorch CPU Latency         : {torch_duration:.2f} ms / image")
    print(f"ONNX Runtime CPU Latency    : {onnx_duration:.2f} ms / image")
    print(f"Achieved Speedup Factor     : {speedup:.2f}x")
    print("="*50)

    # Clean up generated test ONNX file
    if os.path.exists(onnx_path):
        os.remove(onnx_path)

if __name__ == "__main__":
    benchmark_inference(iterations=100)