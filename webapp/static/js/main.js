const form = document.getElementById("predict-form");
const imageInput = document.getElementById("image-input");
const dropzone = document.getElementById("dropzone");
const dropzoneContent = document.getElementById("dropzone-content");
const previewWrap = document.getElementById("preview-wrap");
const previewImg = document.getElementById("preview-img");
const previewName = document.getElementById("preview-name");
const clearBtn = document.getElementById("clear-btn");
const changeBtn = document.getElementById("change-btn");
const predictBtn = document.getElementById("predict-btn");
const spinner = document.getElementById("spinner");
const results = document.getElementById("results");
const errorBox = document.getElementById("error-box");

const RING_CIRCUMFERENCE = 2 * Math.PI * 52;
const MAX_BYTES = 16 * 1024 * 1024;
const ALLOWED_TYPES = new Set([
  "image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif", "image/tiff",
]);
const ALLOWED_EXT = /\.(jpe?g|png|webp|bmp|gif|tiff?)$/i;

let selectedFile = null;

const GENUS_COLORS = {
  Aedes: { bg: "rgba(196,86,106,0.14)", color: "#8a2a3e", border: "rgba(196,86,106,0.35)" },
  Anopheles: { bg: "rgba(125,98,168,0.14)", color: "#4a3570", border: "rgba(125,98,168,0.35)" },
  Culex: { bg: "rgba(45,154,114,0.14)", color: "#1a5c44", border: "rgba(45,154,114,0.35)" },
  Psorophora: { bg: "rgba(200,135,30,0.14)", color: "#7a5208", border: "rgba(200,135,30,0.35)" },
  Uranotaenia: { bg: "rgba(90,171,150,0.14)", color: "#2d6b5c", border: "rgba(90,171,150,0.35)" },
  Toxorhynchites: { bg: "rgba(61,138,120,0.14)", color: "#1f5248", border: "rgba(61,138,120,0.35)" },
  Coquillettidia: { bg: "rgba(184,106,56,0.14)", color: "#6b3a12", border: "rgba(184,106,56,0.35)" },
  default: { bg: "rgba(45,154,114,0.12)", color: "#1a5c44", border: "rgba(45,154,114,0.3)" },
};

const BAR_COLORS = ["bar-1", "bar-2", "bar-3", "bar-4", "bar-5"];

function extractGenus(className) {
  if (className.startsWith("Ae_")) return "Aedes";
  const parts = className.replace(/ /g, "_").split("_");
  return parts[0] || "Unknown";
}

function formatSpecies(className) {
  return className.replace(/_/g, " ");
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function isAllowedFile(file) {
  if (!file) return false;
  if (ALLOWED_TYPES.has(file.type)) return true;
  return ALLOWED_EXT.test(file.name);
}

function syncInputFiles(file) {
  try {
    const dt = new DataTransfer();
    dt.items.add(file);
    imageInput.files = dt.files;
  } catch {
    /* selectedFile is used directly on submit */
  }
}

function setSelectedFile(file) {
  if (!file) return;

  if (!isAllowedFile(file)) {
    showError("Unsupported file type. Please upload JPEG, PNG, WebP, BMP, GIF, or TIFF.");
    return;
  }

  if (file.size > MAX_BYTES) {
    showError("File is too large. Maximum size is 16 MB.");
    return;
  }

  hideError();
  selectedFile = file;
  syncInputFiles(file);

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewName.textContent = file.name;
    previewWrap.classList.remove("hidden");
    dropzoneContent.classList.add("hidden");
    predictBtn.disabled = false;
  };
  reader.onerror = () => showError("Could not read the image file. Please try another.");
  reader.readAsDataURL(file);
}

function clearSelectedFile() {
  selectedFile = null;
  imageInput.value = "";
  previewImg.src = "";
  previewName.textContent = "";
  previewWrap.classList.add("hidden");
  dropzoneContent.classList.remove("hidden");
  predictBtn.disabled = true;
}

function ensureRingGradient() {
  const svg = document.getElementById("confidence-ring");
  if (!svg || svg.querySelector("#ringGradient")) return;
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2d9a72"/>
      <stop offset="50%" stop-color="#5aab96"/>
      <stop offset="100%" stop-color="#7d62a8"/>
    </linearGradient>`;
  svg.prepend(defs);
}

ensureRingGradient();

clearBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  clearSelectedFile();
});

changeBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  imageInput.click();
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", (e) => {
  if (!dropzone.contains(e.relatedTarget)) {
    dropzone.classList.remove("dragover");
  }
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  const file = e.dataTransfer?.files?.[0];
  if (file) setSelectedFile(file);
});

imageInput.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  if (file) setSelectedFile(file);
});

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

function setLoading(loading) {
  predictBtn.disabled = loading || !selectedFile;
  spinner.classList.toggle("hidden", !loading);
  document.querySelector(".btn-text").textContent = loading ? "Analyzing specimen…" : "Predict species";
  document.querySelector(".btn-icon").textContent = loading ? "⏳" : "🔍";
}

function fmtPct(v) {
  if (v == null) return "—";
  return (v * 100).toFixed(1) + "%";
}

function setConfidenceRing(pct) {
  const ring = document.getElementById("ring-fill");
  const center = document.getElementById("ring-center");
  if (!ring || !center) return;
  const offset = RING_CIRCUMFERENCE - (pct / 100) * RING_CIRCUMFERENCE;
  ring.style.strokeDashoffset = offset;
  center.textContent = pct.toFixed(1) + "%";
}

function setGenusBadge(className) {
  const badge = document.getElementById("genus-badge");
  if (!badge) return;
  const genus = extractGenus(className);
  const style = GENUS_COLORS[genus] || GENUS_COLORS.default;
  badge.textContent = genus;
  badge.style.background = style.bg;
  badge.style.color = style.color;
  badge.style.border = `1px solid ${style.border}`;
  badge.classList.remove("hidden");
}

function renderDiseaseChips(diseases) {
  if (!diseases?.length) return "—";
  return diseases
    .map((d) => `<span class="disease-chip">${escapeHtml(d)}</span>`)
    .join("");
}

function renderFact(el, fact, className) {
  const riskClass = fact.risk_class || "risk-moderate";
  el.innerHTML = `
    <div class="fact-tile tile-name">
      <div class="ft-icon">🏷️</div>
      <div class="ft-label">Common name</div>
      <div class="ft-value">${escapeHtml(fact.common_name)}</div>
    </div>
    <div class="fact-tile tile-taxonomy">
      <div class="ft-icon">🧬</div>
      <div class="ft-label">Taxonomy</div>
      <div class="ft-value">
        <strong>${escapeHtml(fact.genus)}</strong> · ${escapeHtml(fact.family || "Culicidae")}<br />
        <em>${escapeHtml(fact.scientific_name || formatSpecies(className))}</em>
      </div>
    </div>
    <div class="fact-tile tile-region">
      <div class="ft-icon">🌍</div>
      <div class="ft-label">Geographic range</div>
      <div class="ft-value">${escapeHtml(fact.region)}</div>
    </div>
    <div class="fact-tile tile-vector">
      <div class="ft-icon">⚕️</div>
      <div class="ft-label">Vector &amp; health impact</div>
      <div class="ft-value">${escapeHtml(fact.vector_status)}</div>
    </div>
    <div class="fact-tile tile-diseases">
      <div class="ft-icon">🦠</div>
      <div class="ft-label">Associated diseases</div>
      <div class="ft-value disease-chips">${renderDiseaseChips(fact.diseases)}</div>
    </div>
    <div class="fact-tile tile-risk">
      <div class="ft-icon">⚠️</div>
      <div class="ft-label">Risk level</div>
      <div class="ft-value"><span class="risk-badge ${riskClass}">${escapeHtml(fact.risk_level)}</span></div>
    </div>
    <div class="fact-tile tile-habitat">
      <div class="ft-icon">💧</div>
      <div class="ft-label">Breeding habitat</div>
      <div class="ft-value">${escapeHtml(fact.habitat)}</div>
    </div>
    <div class="fact-tile tile-biting">
      <div class="ft-icon">🕐</div>
      <div class="ft-label">Biting behavior</div>
      <div class="ft-value">${escapeHtml(fact.biting_time)}</div>
    </div>
    <div class="fact-tile tile-size">
      <div class="ft-icon">📏</div>
      <div class="ft-label">Typical size</div>
      <div class="ft-value">${escapeHtml(fact.size)}</div>
    </div>
    <div class="fact-tile tile-fact wide-tile">
      <div class="ft-icon">🔍</div>
      <div class="ft-label">Identification</div>
      <div class="ft-value">${escapeHtml(fact.identification || fact.fact)}</div>
    </div>`;
}

function renderMetrics(el, m) {
  el.innerHTML = `
    <div class="metric-tile"><span>Test accuracy</span><strong>${fmtPct(m.test_accuracy)}</strong></div>
    <div class="metric-tile"><span>CV mean accuracy</span><strong>${fmtPct(m.cv_mean_accuracy)}</strong></div>
    <div class="metric-tile"><span>F1 macro</span><strong>${fmtPct(m.test_f1_macro)}</strong></div>
    <div class="metric-tile"><span>F1 weighted</span><strong>${fmtPct(m.test_f1_weighted)}</strong></div>`;
}

function renderGroundTruth(el, gt) {
  const card = document.getElementById("gt-card");
  if (!gt) {
    card.classList.add("hidden");
    return;
  }
  card.classList.remove("hidden");

  if (gt.error) {
    el.innerHTML = `<p class="error-box">${escapeHtml(gt.error)}</p>`;
    return;
  }

  const cls = gt.correct ? "correct" : "incorrect";
  const icon = gt.correct ? "✓" : "✗";
  const gm = gt.ground_truth_test_metrics || {};
  const pm = gt.predicted_class_test_metrics || {};

  el.innerHTML = `
    <div class="gt-result ${cls}">${icon} ${escapeHtml(gt.result)} — predicted <em>${escapeHtml(formatSpecies(gt.predicted))}</em>, actual <em>${escapeHtml(formatSpecies(gt.ground_truth))}</em></div>
    <div class="gt-metrics">
      <div class="gt-metric-box">
        <h3>Ground truth · test set</h3>
        <div class="metric-line"><span>Precision</span><strong>${fmtPct(gm.precision)}</strong></div>
        <div class="metric-line"><span>Recall</span><strong>${fmtPct(gm.recall)}</strong></div>
        <div class="metric-line"><span>F1 score</span><strong>${fmtPct(gm.f1)}</strong></div>
        <div class="metric-line"><span>Support</span><strong>${gm.support ?? "—"}</strong></div>
      </div>
      <div class="gt-metric-box">
        <h3>Predicted class · test set</h3>
        <div class="metric-line"><span>Precision</span><strong>${fmtPct(pm.precision)}</strong></div>
        <div class="metric-line"><span>Recall</span><strong>${fmtPct(pm.recall)}</strong></div>
        <div class="metric-line"><span>F1 score</span><strong>${fmtPct(pm.f1)}</strong></div>
        <div class="metric-line"><span>Support</span><strong>${pm.support ?? "—"}</strong></div>
      </div>
    </div>`;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();

  if (!selectedFile) {
    showError("Please select an image before predicting.");
    return;
  }

  setLoading(true);

  const formData = new FormData();
  formData.append("image", selectedFile, selectedFile.name);
  const groundTruth = document.getElementById("ground-truth").value;
  if (groundTruth) formData.append("ground_truth", groundTruth);

  try {
    const res = await fetch("/api/predict", { method: "POST", body: formData });
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(res.status === 413 ? "File is too large (max 16 MB)." : "Server error. Please try again.");
    }
    if (!res.ok) throw new Error(data.error || "Prediction failed");

    document.getElementById("result-image").src = data.image_data_url;
    document.getElementById("result-filename").textContent = data.filename;
    document.getElementById("result-timestamp").textContent =
      "Analyzed at " + new Date().toLocaleString();

    const top = data.prediction;
    setConfidenceRing(top.top_confidence_pct);
    setGenusBadge(top.top_class);

    document.getElementById("top-prediction").innerHTML = `
      <div class="top-pred-block">
        <div class="species-name">${escapeHtml(formatSpecies(top.top_class))}</div>
        <div class="species-sci">${escapeHtml(top.top_class)}</div>
        <span class="common-name">${escapeHtml(data.fact.common_name)}</span>
      </div>`;

    document.getElementById("pred-list").innerHTML = top.predictions.map((p, i) => `
      <div class="pred-row" style="animation-delay:${i * 0.08}s">
        <span class="pred-rank rank-${i + 1}">${i + 1}</span>
        <span class="pred-name">${escapeHtml(formatSpecies(p.class))}</span>
        <span class="pred-pct">${p.confidence_pct}%</span>
        <div class="pred-bar-wrap">
          <div class="pred-bar ${BAR_COLORS[i]}" style="width:0%" data-width="${p.confidence_pct}%"></div>
        </div>
      </div>`).join("");

    requestAnimationFrame(() => {
      document.querySelectorAll(".pred-bar").forEach((bar) => {
        bar.style.width = bar.dataset.width;
      });
    });

    renderFact(document.getElementById("fact-content"), data.fact, top.top_class);
    renderGroundTruth(document.getElementById("gt-content"), data.ground_truth_evaluation);
    renderMetrics(document.getElementById("model-metrics-ref"), data.model_metrics);

    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showError(err.message || "Upload failed. Check your connection and try again.");
  } finally {
    setLoading(false);
  }
});

/* ── Disease info modal ── */
const diseaseDataEl = document.getElementById("disease-data");
const DISEASE_DATA = diseaseDataEl ? JSON.parse(diseaseDataEl.textContent) : {};

const diseaseModal = document.getElementById("disease-modal");
const diseaseModalTitle = document.getElementById("disease-modal-title");
const diseaseModalBody = document.getElementById("disease-modal-body");
const diseaseModalLink = document.getElementById("disease-modal-link");
const diseaseModalClose = document.getElementById("disease-modal-close");
const diseaseModalBackdrop = document.getElementById("disease-modal-backdrop");

function openDiseaseModal(slug) {
  const d = DISEASE_DATA[slug];
  if (!d || !diseaseModal) return;

  diseaseModalTitle.textContent = d.name;
  diseaseModalBody.innerHTML = `
    <p class="disease-summary">${escapeHtml(d.summary)}</p>
    <dl class="disease-details">
      <div><dt>Symptoms</dt><dd>${escapeHtml(d.symptoms)}</dd></div>
      <div><dt>Vectors</dt><dd>${escapeHtml(d.vectors)}</dd></div>
      <div><dt>Regions</dt><dd>${escapeHtml(d.regions)}</dd></div>
      <div><dt>Prevention</dt><dd>${escapeHtml(d.prevention)}</dd></div>
    </dl>
    <p class="disease-source">Source: ${escapeHtml(d.source)}</p>`;

  if (d.url) {
    diseaseModalLink.href = d.url;
    diseaseModalLink.textContent = `Learn more from ${d.source} →`;
    diseaseModalLink.classList.remove("hidden");
  } else {
    diseaseModalLink.classList.add("hidden");
  }

  diseaseModal.classList.remove("hidden");
  document.body.classList.add("modal-open");
}

function closeDiseaseModal() {
  if (!diseaseModal) return;
  diseaseModal.classList.add("hidden");
  document.body.classList.remove("modal-open");
}

diseaseModalClose?.addEventListener("click", closeDiseaseModal);
diseaseModalBackdrop?.addEventListener("click", closeDiseaseModal);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !diseaseModal?.classList.contains("hidden")) {
    closeDiseaseModal();
  }
});

document.querySelectorAll(".disease-tag[data-disease]").forEach((btn) => {
  btn.addEventListener("click", () => openDiseaseModal(btn.dataset.disease));
});
