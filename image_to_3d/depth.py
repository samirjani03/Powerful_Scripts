import torch
import torchvision.transforms as T
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"

model = torch.hub.load(
    "intel-isl/MiDaS", "DPT_Large", trust_repo=True
).to(device)
model.eval()

transform = torch.hub.load(
    "intel-isl/MiDaS", "transforms", trust_repo=True
).dpt_transform

def estimate_depth(image_path):
    img = Image.open(image_path).convert("RGB")
    input_batch = transform(img).to(device)

    with torch.no_grad():
        depth = model(input_batch)

    depth = torch.nn.functional.interpolate(
        depth.unsqueeze(1),
        size=img.size[::-1],
        mode="bicubic",
        align_corners=False,
    ).squeeze()

    return depth.cpu().numpy()
    