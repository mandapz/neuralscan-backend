"""
NeuralScan inference engine.

Model file:
ResNet50_best.pth

Hugging Face repository:
cloud9pix/neuralscan-resnet50

ImageFolder alphabetical sort:
fake=0, real=1
"""

import os
import io
import logging

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_SIZE = (224, 224)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

FAKE_IDX, REAL_IDX = 0, 1

_model = None
_device = None


def _build_resnet50():
    import torch.nn as nn
    from torchvision import models

    class ResNet50Wrapper(nn.Module):
        def __init__(self, num_classes=2):
            super().__init__()

            base = models.resnet50(weights=None)

            self.layer0 = nn.Sequential(
                base.conv1,
                base.bn1,
                base.relu,
                base.maxpool
            )

            self.layer1 = base.layer1
            self.layer2 = base.layer2
            self.layer3 = base.layer3
            self.layer4 = base.layer4

            self.avgpool = base.avgpool

            self.classifier = nn.Sequential(
                nn.Linear(base.fc.in_features, 512),
                nn.ReLU(inplace=True),
                nn.Dropout(0.4),
                nn.Linear(512, num_classes)
            )

        def forward(self, x):
            x = self.layer0(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            x = self.avgpool(x)

            return self.classifier(x.flatten(1))

    return ResNet50Wrapper(num_classes=2)


def _get_model_path():
    """
    Menentukan lokasi model.

    Prioritas:
    1. MODEL_PATH jika file sudah tersedia.
    2. Download ResNet50_best.pth dari Hugging Face.
    """

    # --------------------------------------------------
    # 1. Cek MODEL_PATH
    # --------------------------------------------------
    model_path = os.environ.get(
        "MODEL_PATH",
        "./model/ResNet50_best.pth"
    )

    if os.path.exists(model_path):
        logger.info(
            "Model ditemukan secara lokal: %s",
            model_path
        )
        return model_path

    # --------------------------------------------------
    # 2. Download dari Hugging Face
    # --------------------------------------------------
    repo_id = os.environ.get(
        "HF_MODEL_REPO",
        "cloud9pix/neuralscan-resnet50"
    )

    filename = "ResNet50_best.pth"

    logger.info(
        "Model tidak ditemukan secara lokal."
    )

    logger.info(
        "Mengunduh model dari Hugging Face: %s",
        repo_id
    )

    from huggingface_hub import hf_hub_download

    model_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename
    )

    logger.info(
        "Model berhasil diunduh: %s",
        model_path
    )

    return model_path


def _load_model():
    global _model, _device

    # Jika model sudah pernah dimuat,
    # gunakan model yang sama.
    if _model is not None:
        return _model

    import torch

    # --------------------------------------------------
    # Device
    # --------------------------------------------------
    if torch.backends.mps.is_available():
        _device = torch.device("mps")

    elif torch.cuda.is_available():
        _device = torch.device("cuda")

    else:
        _device = torch.device("cpu")

    logger.info(
        "Inference device: %s",
        _device
    )

    try:
        # --------------------------------------------------
        # Ambil lokasi model
        # --------------------------------------------------
        model_path = _get_model_path()

        # --------------------------------------------------
        # Load checkpoint
        # --------------------------------------------------
        logger.info(
            "Loading model: %s",
            model_path
        )

        ckpt = torch.load(
            model_path,
            map_location=_device,
            weights_only=False
        )

        # --------------------------------------------------
        # Build architecture
        # --------------------------------------------------
        model = _build_resnet50().to(_device)

        # --------------------------------------------------
        # Load state dictionary
        # --------------------------------------------------
        if isinstance(ckpt, dict) and "model_state" in ckpt:

            model.load_state_dict(
                ckpt["model_state"]
            )

            logger.info(
                "Model loaded | epoch=%s val_acc=%s device=%s",
                ckpt.get("epoch", "?"),
                ckpt.get("val_acc", "?"),
                _device
            )

        else:

            model.load_state_dict(ckpt)

            logger.info(
                "Model loaded from raw state_dict | device=%s",
                _device
            )

        # --------------------------------------------------
        # Evaluation mode
        # --------------------------------------------------
        model.eval()

        _model = model

        return _model

    except Exception as e:

        logger.exception(
            "Failed to load model: %s",
            e
        )

        raise RuntimeError(
            f"Model gagal dimuat: {e}"
        ) from e


def preprocess(image_bytes: bytes):
    import torch

    img = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    # Resize sesuai preprocessing training
    img = img.resize(
        IMAGE_SIZE,
        Image.LANCZOS
    )

    # ImageNet normalization
    arr = (
        np.array(
            img,
            dtype=np.float32
        ) / 255.0
        - IMAGENET_MEAN
    ) / IMAGENET_STD

    return torch.tensor(
        arr,
        dtype=torch.float32
    ).permute(
        2,
        0,
        1
    ).unsqueeze(0)


def run_inference(image_bytes: bytes) -> dict:

    import torch

    model = _load_model()

    tensor = preprocess(
        image_bytes
    ).to(_device)

    with torch.no_grad():

        probs = torch.softmax(
            model(tensor),
            dim=1
        )[0]

        p_fake = float(
            probs[FAKE_IDX]
        )

        p_real = float(
            probs[REAL_IDX]
        )

    is_ai = p_fake >= p_real

    raw_score = (
        p_fake
        if is_ai
        else p_real
    )

    return {
        "label": "AI" if is_ai else "Real",
        "confidence": int(
            round(raw_score * 100)
        ),
        "raw_score": raw_score
    }


def make_thumbnail(
    image_bytes: bytes,
    width: int = 240
) -> bytes:

    img = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    h = max(
        1,
        int(
            img.height
            * width
            / img.width
        )
    )

    img = img.resize(
        (width, h),
        Image.LANCZOS
    )

    buf = io.BytesIO()

    img.save(
        buf,
        format="JPEG",
        quality=72
    )

    return buf.getvalue()


def get_image_dimensions(
    image_bytes: bytes
) -> tuple:

    return Image.open(
        io.BytesIO(image_bytes)
    ).size