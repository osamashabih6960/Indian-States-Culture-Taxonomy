# IndiaCulFair: Indian Culture Research Data Curator & Validation Pipeline

**IndiaCulFair** is a dataset curation, audit, and validation framework designed for cultural fairness and precision benchmarking across Indian states and cultural domains.

Targeting an exact research distribution of **7 Indian States** × **7 Cultural Categories** × **200 Unique Verified Images** = **9,800 Approved Images**.

---

## 🏛️ Taxonomy & Coverage

### 7 Target States (Strictly Non-UT)
1. **Kerala**
2. **Rajasthan**
3. **Assam**
4. **Goa**
5. **Bihar**
6. **Telangana**
7. **Sikkim**

### 7 Cultural Categories
- **C1: Festivals** (e.g., Onam, Thrissur Pooram, Bihu, Pushkar, Bonalu, Losoong, Chhath Puja)
- **C2: Monuments** (e.g., Bekal Fort, Hawa Mahal, Rang Ghar, Basilica of Bom Jesus, Golconda Fort)
- **C3: Attire** (e.g., Kasavu Mundu, Poswal/Odhna, Mekhela Chador, Kunbi Sari, Pochampally Ikat)
- **C4: Cuisine** (e.g., Sadya, Dal Baati Churma, Khaar, Goan Fish Curry, Hyderabadi Biryani, Litti Chokha)
- **C5: Art & Crafts** (e.g., Aranmula Kannadi, Blue Pottery, Assamese Bell Metal, Nirmal Paintings, Madhubani)
- **C6: Cultural Symbols** (e.g., Nilavilakku, Jaapi, Ghoomar symbols, Kakatiya Kala Thoranam)
- **C7: Communities** (e.g., Marwaris, Ahoms, Lepchas, Tharus, Lambadas)

---

## 🛡️ 10 Validation Gates (G1 - G10)

Every candidate image passes through a strict 10-gate validation pipeline:

| Gate | Verification Check |
|---|---|
| **G1** | File integrity & technical usability (decodable, dimensions, non-blank) |
| **G2** | Visual content aligns with assigned top-level category |
| **G3** | Claimed cultural concept matches visual evidence |
| **G4** | State association supported by reliable regional evidence |
| **G5** | Individual image license verified and permitted (CC BY, CC BY-SA, Public Domain) |
| **G6** | No exact SHA-256 duplicate exists in the dataset |
| **G7** | No perceptual near-duplicates (pHash distance check) |
| **G8** | Aspect ratio and resolution quality standards |
| **G9** | Two-pass critique against confounding or non-state representations |
| **G10** | Quota adherence (200 unique approved items per cell) |

---

## 🚀 Usage

### 1. Run Pipeline Self-Test
```bash
python3 main.py test
```

### 2. Audit a Directory or Archive
```bash
# Audit an extracted directory
python3 main.py audit --dir /path/to/extracted_folder

# Audit an unextracted ZIP archive
python3 main.py audit --archive /path/to/archive.zip
```

### 3. Re-Audit and Regenerate Reports & Gallery
```bash
python3 main.py re-audit
```

### 4. Collect Verified Images
```bash
python3 main.py collect --state Kerala --category Cuisine --target 200
```

---

## 📊 Reports & Gallery

Running audits generates comprehensive reporting under `reports/`:
- `baseline_image_audit.csv`
- `approved_images.csv`
- `quarantine_manifest.csv`
- `rejected_images.csv`
- `duplicate_audit.csv`
- `image_quality_audit.csv`
- `license_audit.csv`
- `progress_matrix.csv` / `progress_matrix.xlsx`
- `final_validation_summary.json`
- `review_gallery.html` (Interactive visual inspection gallery)

---

## 📁 Repository Structure

```
├── main.py                     # CLI entrypoint
├── src/
│   ├── config.py               # Taxonomies, paths, gate rules
│   ├── audit/                  # Dataset auditor & report generation
│   ├── collector/              # Automated candidate downloaders
│   ├── gallery/                # HTML review gallery generator
│   └── validator/              # Gate validation pipeline (G1–G10)
├── scripts/
│   └── run_pilot_audit.py      # Pilot dataset audit script
├── tests/
│   └── test_validation_pipeline.py
├── reports/                    # Audit logs, manifests, and HTML gallery
├── .gitignore
└── README.md
```
