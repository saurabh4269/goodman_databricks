from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    import streamlit_shadcn_ui as ui

    HAS_SHADCN = True
except Exception:
    HAS_SHADCN = False

from dpdp_kavach.pipeline import CompliancePipeline

st.set_page_config(page_title="DPDP Kavach", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
    * { font-family: "Manrope", system-ui, sans-serif; }

    :root {
      --ink:#0f172a;
      --sub:#64748b;
      --bg:#f8fafc;
      --line:#e2e8f0;
      --card:#ffffff;
      --accent:#0f766e;
      --accent-2:#0ea5e9;
    }

    .stApp {
      background:
        radial-gradient(circle at 10% 10%, #dbeafe 0%, transparent 30%),
        radial-gradient(circle at 90% 0%, #dcfce7 0%, transparent 25%),
        var(--bg);
    }

    .shell {
      border: 1px solid var(--line);
      border-radius: 20px;
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
      padding: 1.2rem 1.3rem;
      margin-bottom: 0.9rem;
    }

    .hero-title {
      font-size: 2rem;
      font-weight: 800;
      color: var(--ink);
      line-height: 1.1;
      margin: 0;
      letter-spacing: 0.01em;
    }

    .hero-sub {
      margin: 0.45rem 0 0 0;
      color: var(--sub);
      font-size: 0.96rem;
    }

    .section {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--ink);
      margin: 0.2rem 0 0.8rem 0;
    }

    .left-nav-label {
      color: #334155;
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }

    .block-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 0.9rem 1rem;
      margin-bottom: 0.6rem;
    }

    div[data-testid="stSidebar"] {
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    }

    div[data-baseweb="tab-list"] { gap: 0.35rem; }
    button[data-baseweb="tab"] {
      border-radius: 10px !important;
      border: 1px solid #dbe4ef !important;
      background: #fff !important;
      padding: 0.35rem 0.65rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
      background: #f0fdfa !important;
      border-color: #99f6e4 !important;
      box-shadow: inset 0 0 0 1px #99f6e4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pipeline = CompliancePipeline(base_dir=Path("src/dpdp_kavach"))

if "grievance_log" not in st.session_state:
    st.session_state.grievance_log = []
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "scan_zip_path" not in st.session_state:
    st.session_state.scan_zip_path = None

with st.sidebar:
    st.markdown("<div class='left-nav-label'>Workspace</div>", unsafe_allow_html=True)
    _ = st.radio(
        "",
        options=["Home", "Data Inventory", "Obligations", "Conflicts", "Grounding", "Artifacts", "Grievance", "Audit"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("<div class='left-nav-label'>Scan Config</div>", unsafe_allow_html=True)
    business_name = st.text_input("Business Name", value="Demo MSME")
    sector = st.selectbox("Sector", options=["fintech", "healthtech", "general"], index=0)
    language = st.selectbox("Output Language", options=["English", "Hindi", "Marathi", "Tamil"], index=0)
    uploaded_file = st.file_uploader("Schema / Data File", type=["sql", "csv", "json"])
    run_clicked = st.button("Run Compliance Scan", type="primary", use_container_width=True)

if run_clicked and uploaded_file is None:
    st.warning("Upload a `.sql`, `.csv`, or `.json` file to continue.")

if run_clicked and uploaded_file is not None:
    staging_dir = Path("artifacts") / "uploads"
    staging_dir.mkdir(parents=True, exist_ok=True)
    schema_path = staging_dir / uploaded_file.name
    schema_path.write_bytes(uploaded_file.getbuffer())

    with st.spinner("Running discovery, obligation mapping, conflict detection, and kit generation..."):
        result, zip_path = pipeline.run(
            schema_path=schema_path,
            business_name=business_name,
            sector=sector,
            language=language,
            artifact_output_dir=Path("artifacts"),
        )
        st.session_state.scan_result = pipeline.to_serializable(result)
        st.session_state.scan_zip_path = str(zip_path)

serializable = st.session_state.scan_result
zip_path = Path(st.session_state.scan_zip_path) if st.session_state.scan_zip_path else None

st.markdown("<div class='shell'>", unsafe_allow_html=True)
st.markdown("<h1 class='hero-title'>DPDP Kavach Dashboard</h1>", unsafe_allow_html=True)

if HAS_SHADCN:
    ui.badges(
        badge_list=[("shadcn", "secondary"), ("in", "outline"), ("streamlit", "destructive")],
        key="hero_badges",
    )
else:
    st.caption("shadcn • streamlit")

st.markdown(
    "<p class='hero-sub'>Compliance intelligence for MSMEs: scan schema, map DPDP obligations, detect cross-law conflicts, and generate downloadable kits.</p>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if serializable is None:
    st.info("Upload a file from the left panel and click `Run Compliance Scan`.")
    st.stop()

metrics = serializable["metrics"]

mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    if HAS_SHADCN:
        ui.metric_card(title="Fields Scanned", content=str(metrics["fields_scanned"]), description="Inventory depth", key="m1")
    else:
        st.metric("Fields Scanned", metrics["fields_scanned"])
with mc2:
    if HAS_SHADCN:
        ui.metric_card(title="Obligations", content=str(metrics["obligation_count"]), description="Triggered controls", key="m2")
    else:
        st.metric("Obligations", metrics["obligation_count"])
with mc3:
    if HAS_SHADCN:
        ui.metric_card(title="Conflicts", content=str(metrics["conflict_count"]), description="Cross-law flags", key="m3")
    else:
        st.metric("Conflicts", metrics["conflict_count"])
with mc4:
    if HAS_SHADCN:
        ui.metric_card(title="Grounding", content=f"{metrics['grounding_score']:.0%}", description="Legal confidence", key="m4")
    else:
        st.metric("Grounding", f"{metrics['grounding_score']:.0%}")

if HAS_SHADCN:
    selected_view = ui.tabs(
        options=["overview", "inventory", "obligations", "conflicts", "grounding", "artifacts", "grievance", "audit"],
        default_value="overview",
        key="main_view_tabs",
    )
else:
    selected_view = st.selectbox(
        "View",
        ["overview", "inventory", "obligations", "conflicts", "grounding", "artifacts", "grievance", "audit"],
    )

if selected_view == "overview":
    st.markdown("<div class='section'>Overview</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='block-card'><b>Business</b><br>" + serializable["business_name"] + "</div>", unsafe_allow_html=True)
        st.markdown("<div class='block-card'><b>Sector</b><br>" + serializable["sector"] + "</div>", unsafe_allow_html=True)
    with c2:
        if HAS_SHADCN:
            ui.date_picker(label="Demo Date", key="overview_date")
        else:
            st.date_input("Demo Date")

elif selected_view == "inventory":
    st.markdown("<div class='section'>Classified Data Inventory</div>", unsafe_allow_html=True)
    df = pd.DataFrame(serializable["classified_elements"])
    if HAS_SHADCN:
        ui.table(data=df, maxHeight=560, key="inventory_table")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

elif selected_view == "obligations":
    st.markdown("<div class='section'>Triggered Obligations</div>", unsafe_allow_html=True)
    obligation_df = pd.DataFrame(serializable["obligations"])
    if HAS_SHADCN:
        ui.table(data=obligation_df, maxHeight=520, key="obligation_table")
    else:
        st.dataframe(obligation_df, use_container_width=True, hide_index=True)

elif selected_view == "conflicts":
    st.markdown("<div class='section'>Cross-Law Conflicts</div>", unsafe_allow_html=True)
    if serializable["conflicts"]:
        for i, conflict in enumerate(serializable["conflicts"]):
            if HAS_SHADCN:
                ui.card(
                    title=conflict["regulation"],
                    content=conflict["summary"],
                    description=f"DPDP: {conflict['dpdp_section']} | Resolution: {conflict['resolution']}",
                    key=f"conflict_{i}",
                )
            else:
                st.markdown(f"**{conflict['regulation']}**\n\n{conflict['summary']}\n\nResolution: {conflict['resolution']}")
    else:
        st.info("No conflicts detected.")

elif selected_view == "grounding":
    st.markdown("<div class='section'>Grounding Confidence</div>", unsafe_allow_html=True)
    st.progress(min(max(float(metrics["grounding_score"]), 0.0), 1.0))
    grounding_df = pd.DataFrame(serializable["grounding_report"])
    if HAS_SHADCN:
        ui.table(data=grounding_df, maxHeight=560, key="grounding_table")
    else:
        st.dataframe(grounding_df, use_container_width=True, hide_index=True)

elif selected_view == "artifacts":
    st.markdown("<div class='section'>Compliance Kit Artifacts</div>", unsafe_allow_html=True)
    for name, content in serializable["artifacts"].items():
        with st.expander(name, expanded=False):
            st.code(content, language="markdown")
    if zip_path and zip_path.exists():
        with zip_path.open("rb") as handle:
            st.download_button(
                "Download Compliance Kit (ZIP)",
                data=handle.read(),
                file_name=zip_path.name,
                mime="application/zip",
            )

elif selected_view == "grievance":
    st.markdown("<div class='section'>Section 11-14 Grievance Intake Demo</div>", unsafe_allow_html=True)
    with st.form("grievance_form"):
        request_type = st.selectbox("Request Type", ["Access", "Correction", "Erasure", "Nomination", "Complaint"])
        principal_id = st.text_input("Data Principal ID", "dp-001")
        details = st.text_area("Request Details", "Please process this DPDP request.")
        submitted = st.form_submit_button("Submit Request")
    if submitted:
        st.session_state.grievance_log.append(
            {"request_type": request_type, "principal_id": principal_id, "details": details}
        )
        st.success("Request logged in demo workflow.")
    if st.session_state.grievance_log:
        log_df = pd.DataFrame(st.session_state.grievance_log)
        if HAS_SHADCN:
            ui.table(data=log_df, maxHeight=420, key="grievance_table")
        else:
            st.dataframe(log_df, use_container_width=True, hide_index=True)

elif selected_view == "audit":
    st.markdown("<div class='section'>Audit JSON</div>", unsafe_allow_html=True)
    st.code(json.dumps(serializable, indent=2), language="json")
