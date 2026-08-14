"""
Hardcoded description pool for NeuralScan detection results.
No external API needed — random selection from curated pools.
"""
import random

# ── AI-Generated pools ─────────────────────────────────────────────────────

AI_DESCRIPTIONS = [
    "Gambar ini memperlihatkan tekstur yang terlalu halus dan seragam, tanpa detail mikroskopis seperti pori kulit atau ketidaksempurnaan alami yang biasanya ditemukan pada foto nyata. Distribusi noise yang terlalu merata di seluruh area gambar adalah ciri khas keluaran model generatif.",
    "Analisis frekuensi gambar menunjukkan pola yang konsisten dengan output model diffusion. Tepi-tepi objek memiliki sedikit halo yang tidak wajar, dan detail halus seperti rambut atau tekstur kain tampak dihasilkan secara algoritmik daripada difoto secara optik.",
    "Gambar ini menunjukkan simetri yang terlalu sempurna dan pencahayaan yang tidak alami. Bayangan tidak konsisten dengan sumber cahaya tunggal yang logis, dan area latar belakang memiliki elemen yang berulang secara halus — karakteristik umum pada gambar hasil generasi AI.",
    "Distribusi piksel pada gambar ini menunjukkan fingerprint statistik yang berbeda dari fotografi kamera nyata. Tidak ada aberasi kromatik pada tepi kontras tinggi, dan bokeh terlihat dihasilkan secara matematis bukan secara optis dari lensa fisik.",
    "Pola noise pada gambar ini terlalu seragam untuk berasal dari sensor kamera. Model generatif modern menghasilkan noise sintetis yang terlihat halus secara visual, namun tidak memiliki variasi acak yang sesungguhnya seperti pada foto dari kamera nyata.",
    "Gambar ini mengandung artefak kompresi yang tidak konsisten dengan bagaimana gambar nyata biasanya terkompresi. Selain itu, detail pada area peripheral gambar tampak dibuat secara algoritmik dengan tingkat kerincian yang sama di seluruh frame.",
    "Analisis menunjukkan bahwa gambar ini kemungkinan besar dihasilkan oleh model generatif berbasis diffusion. Fitur-fitur seperti konsistensi tekstur yang berlebihan, ketiadaan noise optis alami, dan gradasi warna yang terlalu mulus menjadi indikator utamanya.",
]

AI_SIGNALS = [
    ["Tekstur terlalu halus", "Noise seragam", "Tanpa aberasi kromatik", "Halo artifak pada tepi"],
    ["Simetri berlebihan", "Pencahayaan tidak konsisten", "Pola latar berulang", "GAN fingerprint"],
    ["Bokeh matematis", "Tanpa grain sensor", "Detail algoritmik", "Diffusion artefak"],
    ["Frekuensi piksel tidak natural", "Tidak ada lens distortion", "Gradasi warna sempurna", "Edge artifacts"],
    ["Distribusi noise sintetis", "Tekstur terlalu konsisten", "Warna saturasi seragam", "Pola berulang halus"],
]

# ── Real photo pools ────────────────────────────────────────────────────────

REAL_DESCRIPTIONS = [
    "Gambar ini memiliki karakteristik fotografi nyata yang kuat: noise sensor yang natural, aberasi kromatik halus pada tepi kontras tinggi, dan distribusi fokus yang konsisten dengan lensa optis fisik. Ketidaksempurnaan alami ini adalah tanda gambar diambil dengan kamera sungguhan.",
    "Analisis menunjukkan pola noise yang konsisten dengan sensor kamera digital. Gambar memiliki grain alami, depth-of-field yang organik, dan chromatic aberration di sekitar area terang — semuanya adalah karakteristik fotografi dari dunia nyata.",
    "Gambar ini memperlihatkan tanda-tanda keaslian fotografis: highlight yang natural dengan roll-off gradual, shadow yang mengandung detail tersembunyi, dan micro-texture pada permukaan objek yang menunjukkan variasi acak alami dari materi fisik nyata.",
    "Distribusi frekuensi gambar ini konsisten dengan output sensor kamera. Terdapat lens distortion halus di area tepi frame, serta ketidaksempurnaan kecil dalam pencahayaan yang merupakan ciri khas kondisi cahaya nyata yang tidak dapat dikontrol sempurna.",
    "Gambar ini mengandung fingerprint sensor yang khas dari fotografi nyata. Pola noise, distribusi warna, dan perilaku fokus semuanya konsisten dengan gambar yang diambil dalam kondisi dunia nyata menggunakan perangkat optis fisik.",
    "Analisis piksel menunjukkan variasi tekstur yang organik dan tidak berulang, yang merupakan tanda khas permukaan fisik nyata. Transisi warna dan gradasi cahaya juga menunjukkan interaksi cahaya-materi yang alami, bukan dihasilkan secara komputasional.",
    "Gambar ini memiliki karakteristik autentik dari fotografi: motion blur yang natural, aberasi lensa, dan kompresi JPEG yang konsisten dengan bagaimana kamera nyata memproses dan menyimpan gambar. Tidak ditemukan artefak generatif yang signifikan.",
]

REAL_SIGNALS = [
    ["Noise sensor natural", "Aberasi kromatik", "Depth of field organik", "Grain alami"],
    ["Highlight roll-off natural", "Shadow detail tersembunyi", "Micro-texture variasi", "Lens distortion"],
    ["Fingerprint sensor valid", "Distribusi warna natural", "Fokus alami", "Kompresi konsisten"],
    ["Ketidaksempurnaan pencahayaan", "Variasi tekstur organik", "Gradasi cahaya alami", "Tanpa artefak GAN"],
    ["Detail tepi natural", "Bokeh optis nyata", "Motion blur alami", "Noise tidak seragam"],
]


def get_description(label: str) -> dict:
    """
    Return a random description + signals for the given label.
    label: "AI" | "Real"
    """
    if label == "AI":
        return {
            "description": random.choice(AI_DESCRIPTIONS),
            "signals"    : random.choice(AI_SIGNALS),
        }
    else:
        return {
            "description": random.choice(REAL_DESCRIPTIONS),
            "signals"    : random.choice(REAL_SIGNALS),
        }
