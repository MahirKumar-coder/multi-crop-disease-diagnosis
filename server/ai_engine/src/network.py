import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

class DeepFineTunedEfficientNet(nn.Module):
    def __init__(self, num_classes: int = 38, dropout_rate: float = 0.3):
        super(DeepFineTunedEfficientNet, self).__init__()
        self.model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        in_features = self.model.classifier[1].in_features

        # Replace classification head
        self.model.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(512, num_classes)
        )

    def freeze_all(self):
        """Freezes all backbone feature layers."""
        for param in self.model.features.parameters():
            param.requires_grad = False

    def unfreeze_stages(self, from_stage: int = 4):
        """
        EfficientNet-B0 has 8 feature blocks (0 to 7).
        Unfreezes blocks starting from `from_stage` onwards.
        """
        for i, block in enumerate(self.model.features):
            if i >= from_stage:
                for param in block.parameters():
                    param.requires_grad = True
            else:
                for param in block.parameters():
                    param.requires_grad = False

    def get_parameter_groups(self, backbone_lr: float = 1e-5, head_lr: float = 1e-3, weight_decay: float = 1e-4):
        """Configures differential learning rates for AdamW."""
        backbone_params = [p for p in self.model.features.parameters() if p.requires_grad]
        head_params = list(self.model.classifier.parameters())

        return [
            {"params": backbone_params, "lr": backbone_lr, "weight_decay": weight_decay},
            {"params": head_params, "lr": head_lr, "weight_decay": weight_decay}
        ]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

class PlantDiseaseClassifier(nn.Module):
    def __init__(self, num_classes: int = 38):
        super().__init__()
        base_model = efficientnet_b0(weights=None)
        self.features = base_model.features
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(1280, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(512, num_classes)
        )
        
        class BackboneHelper:
            def __init__(self, features, classifier):
                self.features = features
                self.classifier = classifier
        self.backbone = BackboneHelper(self.features, self.classifier)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = nn.functional.adaptive_avg_pool2d(x, 1)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

    def freeze_backbone(self):
        for param in self.features.parameters():
            param.requires_grad = False

    def unfreeze_top_blocks(self, num_blocks_to_unfreeze=3):
        total_blocks = len(self.features)
        start_idx = total_blocks - num_blocks_to_unfreeze
        for i, block in enumerate(self.features):
            if i >= start_idx:
                for param in block.parameters():
                    param.requires_grad = True
            else:
                for param in block.parameters():
                    param.requires_grad = False