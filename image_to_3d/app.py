# uv pip install -r req.txt --extra-index-url https://download.pytorch.org/whl/cu121         

# python - <<EOF
# import torch
# print("Python:", __import__("sys").version)
# print("CUDA available:", torch.cuda.is_available())
# print("GPU:", torch.cuda.get_device_name(0))
# EOF


from flask import Flask, render_template, request
import os
from depth import estimate_depth
from pointcloud import depth_to_pointcloud

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["image"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        depth = estimate_depth(path)
        output_path = os.path.join(OUTPUT_FOLDER, "model.ply")
        depth_to_pointcloud(depth, output_path)

        return "3D model generated: static/outputs/model.ply"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
