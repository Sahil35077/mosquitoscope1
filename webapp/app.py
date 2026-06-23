import base64
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from webapp.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB, MODEL_PATH, PORT
from webapp.disease_info import DISEASES, get_disease, list_diseases
from webapp.model_service import get_classifier
from webapp.mosquito_facts import get_fact

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    clf = get_classifier()
    return render_template(
        "index.html",
        classes=sorted(clf.classes),
        model_metrics=clf.model_metrics,
        diseases=DISEASES,
    )


@app.route("/api/classes")
def api_classes():
    clf = get_classifier()
    return jsonify({"classes": sorted(clf.classes)})


@app.route("/api/diseases")
def api_diseases():
    return jsonify({"diseases": list_diseases()})


@app.route("/api/diseases/<slug>")
def api_disease(slug):
    disease = get_disease(slug)
    if not disease:
        return jsonify({"error": "Disease not found."}), 404
    return jsonify({"slug": slug, **disease})


@app.route("/api/predict", methods=["POST"])
def api_predict():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    image_bytes = file.read()
    ground_truth = request.form.get("ground_truth", "").strip() or None

    clf = get_classifier()
    result = clf.predict(image_bytes)

    mime = file.mimetype or "image/jpeg"
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    top_class = result["top_class"]
    fact = get_fact(top_class)

    response = {
        "filename": file.filename,
        "image_data_url": f"data:{mime};base64,{image_b64}",
        "prediction": result,
        "fact": fact,
        "model_metrics": clf.model_metrics,
    }

    if ground_truth:
        if ground_truth not in clf.classes:
            response["ground_truth_evaluation"] = {
                "ground_truth": ground_truth,
                "error": "Ground truth label is not in the trained class list.",
            }
        else:
            response["ground_truth_evaluation"] = clf.evaluate_ground_truth(
                top_class, ground_truth
            )

    return jsonify(response)


@app.route("/health")
def health():
    clf = get_classifier()
    return jsonify({
        "status": "ok",
        "device": clf.device,
        "num_classes": len(clf.classes),
        "model_path": str(MODEL_PATH),
        "image_size": clf.image_size,
        "training_recipe": clf.model_metrics.get("training_recipe"),
    })


if __name__ == "__main__":
    print("Loading model...")
    get_classifier()
    print(f"Starting MosquitoScope on http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
