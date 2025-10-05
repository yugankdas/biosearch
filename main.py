from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io, os, re

app = Flask(__name__)

CSV_PATH = os.path.join("static", "data", "Differential_Expression_cleaned.csv")
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
df.columns = [c.strip() for c in df.columns]

def normalize(s: str) -> str:
    return re.sub(r'[^0-9a-z]', '', str(s).lower())

cols_norm_map = {normalize(c): c for c in df.columns}

def find_col(*keywords):
    for k in keywords:
        nk = normalize(k)
        for nc, orig in cols_norm_map.items():
            if nk in nc:
                return orig
    return None

def safe_float(v, default=0.0):
    try:
        if pd.isna(v):
            return default
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        try:
            return float(str(v).replace(",", "").strip())
        except Exception:
            return default

# automatically detect relevant columns (robust)
LOG2_COL = find_col("log2fc", "log2", "log2_fold")
PV_COL   = find_col("pvalue", "p.value", "p_value")
ALL_MEAN_COL = find_col("all.mean", "allmean", "mean")
GROUP_1G_COL = find_col("group.mean_1g", "groupmean1g", "group.mean(1g)")
GROUP_UG_COL = find_col("group.mean_ug", "groupmeanug", "group.mean(ug)")

# normalize SYMBOL
if "SYMBOL" in df.columns:
    df["SYMBOL"] = df["SYMBOL"].astype(str).str.strip().str.lower()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/glossary")
def glossary():
    return render_template("glossary.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
def dashboard():
    return render_template("download.html")

@app.route("/api/search")
def search_api():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])

    mask = df["SYMBOL"].astype(str).str.lower().str.contains(q, na=False)
    if "GENENAME" in df.columns:
        mask |= df["GENENAME"].astype(str).str.lower().str.contains(q, na=False)

    results = df[mask].head(20)

    out = []
    for _, row in results.iterrows():
        out.append({
            "symbol": str(row.get("SYMBOL", "")).upper(),
            "genename": str(row.get("GENENAME", "")),
            "log2fc": safe_float(row.get(LOG2_COL)),
            "p_value": safe_float(row.get(PV_COL)),
            "mean": safe_float(row.get(ALL_MEAN_COL))
        })
    return jsonify(out)

@app.route("/<symbol>")
def gene_detail(symbol):
    s = str(symbol).lower().strip()
    if "SYMBOL" not in df.columns:
        return render_template("gene_detail.html", gene=None, error="No SYMBOL column in CSV")

    result = df[df["SYMBOL"].astype(str).str.lower() == s]
    if result.empty:
        return render_template("gene_detail.html", gene=None, error=f"No data for {symbol.upper()}")

    row = result.iloc[0]
    log2fc = safe_float(row.get(LOG2_COL))
    pval = safe_float(row.get(PV_COL))
    mean = safe_float(row.get(ALL_MEAN_COL))
    mean_1g = safe_float(row.get(GROUP_1G_COL)) if GROUP_1G_COL else None
    mean_ug = safe_float(row.get(GROUP_UG_COL)) if GROUP_UG_COL else None

    # fallback synthetic chart values if group means missing
    if not mean_1g or not mean_ug:
        base = mean or 1.0
        try:
            fold = 2 ** (log2fc)
        except Exception:
            fold = 1.0
        mean_1g = float(base)
        mean_ug = float(base * fold)

    gene = {
        "symbol": str(row.get("SYMBOL", "")).upper(),
        "genename": str(row.get("GENENAME", "")),
        "log2fc": float(log2fc),
        "p_value": float(pval),
        "mean": float(mean),
        # IMPORTANT: ensure these are plain Python lists (not numpy types)
        "chart": {
            "labels": ["Earth (1G)", "Microgravity"],
            "values": [float(mean_1g), float(mean_ug)]
        }
    }
    return render_template("gene_detail.html", gene=gene)

@app.route("/download/<symbol>")
def download_gene(symbol):
    s = str(symbol).lower().strip()
    result = df[df["SYMBOL"].astype(str).str.lower() == s]
    if result.empty:
        return "No data found", 404

    buf = io.StringIO()
    result.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"{symbol.upper()}_data.csv")




@app.route("/ai_summary/<symbol>")
def ai_summary(symbol):
    symbol = symbol.lower().strip()
    result = df[df["SYMBOL"].str.lower() == symbol]
    if result.empty:
        return jsonify({"summary": "No gene data available."})

    row = result.iloc[0]
    gene_name = row.get("GENENAME", "Unknown gene")
    log2fc = row.get("Log2fc_(1G)v(uG_in_HARV_Rotary_Cell_Culture_System)", "N/A")
    pval = row.get("P.value_(1G)v(uG_in_HARV_Rotary_Cell_Culture_System)", "N/A")
    mean = row.get("All.mean", "N/A")

    summary = f"""
    <p><b>{gene_name}</b> ({symbol.upper()}) is a key gene showing measurable transcriptional adaptation when exposed to simulated microgravity compared to standard Earth gravity (1G) conditions.</p>

    <p>In this dataset, the expression change quantified by Log2 Fold Change (Log2FC) is <b>{log2fc}</b>, while the mean transcriptional intensity across conditions is approximately <b>{mean}</b>. 
    The reported p-value of <b>{pval}</b> indicates the statistical significance of this difference, reflecting the confidence in observed gene modulation under microgravity stress.</p>

    <p>Such modulation patterns suggest possible involvement of <b>{gene_name}</b> in gravity-sensitive biological processes, including cell differentiation, DNA repair, and oxidative stress response. 
    These changes could represent early molecular adaptations critical to human spaceflight biology and bioengineering in low-gravity environments.</p>

    <p>This data contributes to understanding how spaceflight conditions alter the expression landscape, 
    guiding future countermeasure development for astronaut health and long-duration missions beyond Earth orbit.</p>
    """

    return jsonify({"summary": summary})

if __name__ == "__main__":
    app.run(debug=True, port=4422)
