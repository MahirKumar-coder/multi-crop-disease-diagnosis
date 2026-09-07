import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = "../ai_engine/models/ieee_report_figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

def create_system_architecture_diagram():
    """Generates the multi-tier Layered System Architecture for Chapter 5."""
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle, color, text_color="white"):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
            facecolor=color, edgecolor="#1e293b", linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + 2.5, title, color=text_color, weight="bold", fontsize=11, ha="center", va="center")
        ax.text(x + w/2, y + h/2 - 3.5, subtitle, color=text_color, fontsize=8.5, ha="center", va="center", style="italic")

    # Layer 1: Client Tier
    draw_box(4, 78, 92, 16, "PRESENTATION TIER (React 18 + Vite SPA)", 
             "Components: Camera Capture | Grad-CAM Split Viewer | Remediation Dosage Tabs | PDF Exporter", "#1E3A8A")

    # Layer 2: API Gateway & Security
    draw_box(4, 52, 92, 18, "APPLICATION & SECURITY GATEWAY (FastAPI + Uvicorn)", 
             "Modules: PureMagic Header Inspection | Pillow Pixel Bound Limiter | SlowAPI Limiter (30 req/min) | SHA-256 Cache", "#047857")

    # Layer 3: Inference & Deep Learning Core
    draw_box(4, 26, 44, 18, "INFERENCE & AI ENGINE", 
             "ONNX Runtime INT8 Engine (5.7MB)\nTemperature Calibrator (T=1.18)\nGuided Grad-CAM (features[7])", "#B45309")

    # Layer 4: Knowledge Base & Persistence
    draw_box(52, 26, 44, 18, "DATA & DOMAIN KNOWLEDGE TIER", 
             "38-Class Remediation Knowledge Base\nDosage & Chemical Schedules\nSQLite Diagnostic Audit History", "#6D28D9")

    # Layer 5: Cloud Hosting Infrastructure
    draw_box(4, 4, 92, 14, "DEPLOYMENT & HOSTING INFRASTRUCTURE", 
             "Client: Vercel CDN Edge Network | Server: Render Cloud Container (Docker Python 3.11-slim, TLS 1.3)", "#374151")

    # Connecting Arrows
    arrow_props = dict(arrowstyle="->", color="#1E293B", lw=2, mutation_scale=15)
    ax.annotate("", xy=(50, 78), xytext=(50, 70), arrowprops=arrow_props)
    ax.annotate("", xy=(26, 52), xytext=(26, 44), arrowprops=arrow_props)
    ax.annotate("", xy=(74, 52), xytext=(74, 44), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 26), xytext=(50, 18), arrowprops=arrow_props)

    plt.title("Fig. 5.1. Multi-Tier End-to-End System Architecture", fontsize=13, fontweight="bold", pad=20)
    
    save_path = os.path.join(OUTPUT_DIR, "fig_5_1_system_architecture_300dpi.png")
    plt.savefig(save_path)
    plt.close()
    print(f"✅ Exported: {save_path}")

def create_data_flow_diagram():
    """Generates the Level-1 Data Flow Diagram (DFD) for Chapter 13."""
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 50)
    ax.axis("off")

    stages = [
        ("1. Ingestion", "UploadFile\nStream", 8, "#2563EB"),
        ("2. Validation", "Magic-Byte &\nDecompression", 33, "#059669"),
        ("3. Caching", "SHA-256 Hash\nTable Lookup", 58, "#D97706"),
        ("4. Execution", "ONNX INT8\nForward Pass", 83, "#DC2626"),
        ("5. Synthesis", "Enrichment &\nGrad-CAM Merge", 108, "#7C3AED"),
    ]

    for title, desc, x, color in stages:
        rect = patches.FancyBboxPatch(
            (x, 15), 18, 20, boxstyle="round,pad=0.8,rounding_size=1.5",
            facecolor=color, edgecolor="#0f172a", linewidth=1.2
        )
        ax.add_patch(rect)
        ax.text(x + 9, 28, title, color="white", weight="bold", fontsize=10, ha="center")
        ax.text(x + 9, 21, desc, color="white", fontsize=8.5, ha="center", style="italic")

    # Link Stages with arrows
    arrow_props = dict(arrowstyle="->", color="#334155", lw=2.2, mutation_scale=16)
    for i in range(len(stages) - 1):
        x_start = stages[i][2] + 18
        x_end = stages[i+1][2]
        ax.annotate("", xy=(x_end, 25), xytext=(x_start, 25), arrowprops=arrow_props)

    plt.title("Fig. 13.1. Level-1 Data Pipeline & Inference Sequence (POST /api/predict)", fontsize=13, fontweight="bold", pad=20)

    save_path = os.path.join(OUTPUT_DIR, "fig_13_1_data_flow_sequence_300dpi.png")
    plt.savefig(save_path)
    plt.close()
    print(f"✅ Exported: {save_path}")

if __name__ == "__main__":
    create_system_architecture_diagram()
    create_data_flow_diagram()