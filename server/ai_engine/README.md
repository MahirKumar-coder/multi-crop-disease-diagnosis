# AI Engine: Multi-Crop Plant Disease Diagnosis & Explainability

This submodule houses the deep learning training pipeline, out-of-distribution (OOD) robustness evaluation, post-training quantization, temperature calibration, and visual explainability services for the 38-class plant disease diagnosis system.

---

## 1. Network Architecture Overview

The core classifier uses a scaled **EfficientNet-B0** convolutional backbone pre-trained on ImageNet.