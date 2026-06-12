"""
Greatify · File ID Renamer
==========================

Strip the name from a file and keep only the numeric ID.

    250701001-Abhilasha Jha.jpeg   ->   250701001.jpeg

Upload:
  * individual image files  -> each one is renamed
  * a zip file              -> every file INSIDE the zip is renamed and the
                              zip is repacked for download

Styled to the Greatify brand guidelines (Chalkboard Green / Growth Green /
Creme, DM Sans + Lora, Gi logo + watermark).

Run with:
    streamlit run rename_app.py
"""

import base64
import io
import os
import re
import zipfile

import streamlit as st

# --------------------------------------------------------------------------- #
# Brand constants
# --------------------------------------------------------------------------- #
CHALKBOARD = "#00373A"   # primary dark
GROWTH = "#00DC46"       # accent / energy
CREME = "#F9F7E8"        # light bg
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def load_logo_data_uri() -> str:
    """Return the Greatify horizontal logo as a base64 data URI (or '')."""
    path = os.path.join(ASSETS, "logo-webp-base64.txt")
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except OSError:
        return ""


def load_gi_data_uri() -> str:
    """Return the Gi symbol PNG as a base64 data URI for the watermark (or '')."""
    path = os.path.join(ASSETS, "gi-symbol-on-white.png")
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except OSError:
        return ""


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #
def extract_id(filename: str) -> str | None:
    """Return the numeric ID from a file name, or None if there isn't one.

        "250701001-Abhilasha Jha.jpeg" -> "250701001"
    """
    base = os.path.basename(filename)
    match = re.match(r"\s*(\d+)", base)
    if match:
        return match.group(1)
    match = re.search(r"\d+", base)
    return match.group(0) if match else None


def get_extension(filename: str) -> str:
    """Return the file extension including the dot, e.g. '.jpeg' (lowercased)."""
    name = os.path.basename(filename)
    if "." in name:
        return "." + name.rsplit(".", 1)[-1].lower()
    return ""


def new_name(filename: str) -> str | None:
    """Build the renamed file name, or None if no ID could be found."""
    file_id = extract_id(filename)
    if file_id is None:
        return None
    return f"{file_id}{get_extension(filename)}"


def dedupe(target: str, used_names: dict[str, int]) -> str:
    """Return a collision-free name, adding _1, _2 ... if needed."""
    if target not in used_names:
        used_names[target] = 0
        return target
    used_names[target] += 1
    stem, dot, ext = target.rpartition(".")
    if dot:
        return f"{stem}_{used_names[target]}.{ext}"
    return f"{target}_{used_names[target]}"


def rename_zip(data: bytes) -> tuple[bytes, list[tuple[str, str]], list[str]]:
    """Rename every file inside a zip and repack it.

    Returns (new_zip_bytes, [(old, new), ...], [skipped_names]).
    """
    renamed = []
    skipped = []
    used_names: dict[str, int] = {}

    out_buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as zin, \
            zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            if info.is_dir():
                continue
            base = os.path.basename(info.filename)
            if not base or base.startswith(".") or "__MACOSX" in info.filename:
                continue

            target = new_name(base)
            if target is None:
                skipped.append(info.filename)
                zout.writestr(info.filename, zin.read(info.filename))
                continue

            target = dedupe(target, used_names)
            zout.writestr(target, zin.read(info.filename))
            renamed.append((base, target))

    out_buffer.seek(0)
    return out_buffer.getvalue(), renamed, skipped


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Greatify · File ID Renamer",
    page_icon="🟢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

LOGO = load_logo_data_uri()
GI = load_gi_data_uri()

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap');

/* ---- base : Chalkboard Green canvas with Gi watermark ---- */
.stApp {{
    background:
        radial-gradient(900px 500px at 50% -8%, #0a4a4e 0%, transparent 60%),
        {CHALKBOARD};
    color: #e8efee;
    font-family: 'DM Sans', sans-serif;
}}
.stApp::before {{
    content: "";
    position: fixed; inset: 0;
    background-image: url("{GI}");
    background-repeat: no-repeat;
    background-position: 115% 60%;
    background-size: 620px;
    opacity: 0.05;
    pointer-events: none;
    z-index: 0;
}}
.block-container {{ padding-top: 2rem; max-width: 840px; position: relative; z-index: 1; }}
#MainMenu, header, footer {{ visibility: hidden; }}

/* ---- hero ---- */
.hero {{
    text-align: center;
    padding: 2.4rem 1.5rem 2.2rem;
    border-radius: 26px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(0,220,70,0.18);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    margin-bottom: 1.6rem;
}}
.hero img.logo {{ height: 46px; margin-bottom: 1.4rem; }}
.hero h1 {{
    font-family: 'DM Sans', sans-serif;
    font-size: 2.4rem; font-weight: 800; margin: 0;
    letter-spacing: -0.02em; color: #ffffff;
}}
.hero h1 .accent {{ color: {GROWTH}; }}
.hero .sub {{
    font-family: 'Lora', serif; font-style: italic;
    color: #b8c9c7; margin: .7rem 0 0; font-size: 1.05rem;
}}
.accent-line {{
    width: 60px; height: 3px; background: {GROWTH};
    margin: 1.2rem auto 0; border-radius: 2px;
}}
.hero .chip {{
    display: inline-flex; align-items: center; gap: .5rem;
    margin-top: 1.3rem; padding: .5rem 1.1rem; border-radius: 999px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .84rem; color: {CREME};
    background: rgba(0,220,70,0.1);
    border: 1px solid rgba(0,220,70,0.35);
}}

/* ---- cards ---- */
.card {{
    background: {CREME};
    color: {CHALKBOARD};
    border-radius: 18px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 12px 34px rgba(0,0,0,0.35);
}}
.card-title {{
    font-family: 'DM Sans', sans-serif;
    font-weight: 700; font-size: 1.08rem; color: {CHALKBOARD};
    display: flex; align-items: center; gap: .55rem; margin-bottom: 1rem;
    padding-left: .7rem; border-left: 3px solid {GROWTH};
}}

/* rename rows */
.row {{
    display: flex; align-items: center; gap: .6rem; flex-wrap: wrap;
    padding: .55rem .8rem; border-radius: 11px; margin-bottom: .4rem;
    background: rgba(0,55,58,0.05);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .85rem;
}}
.row .old {{ color: #5a6b6c; text-decoration: line-through; }}
.row .arrow {{ color: {GROWTH}; font-weight: 800; }}
.row .new {{
    color: {CHALKBOARD}; font-weight: 700;
    background: rgba(0,220,70,0.18); padding: .15rem .55rem; border-radius: 7px;
}}

/* ---- metrics ---- */
.metrics {{ display: flex; gap: .8rem; margin-bottom: 1.3rem; }}
.metric {{
    flex: 1; text-align: center; padding: 1.1rem .5rem; border-radius: 16px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,220,70,0.2);
}}
.metric .num {{
    font-family: 'DM Sans', sans-serif;
    font-size: 2rem; font-weight: 800; line-height: 1; color: {GROWTH};
}}
.metric .lbl {{
    color: #b8c9c7; font-size: .74rem; margin-top: .4rem;
    text-transform: uppercase; letter-spacing: .08em; font-weight: 600;
}}

/* ---- uploader ---- */
[data-testid="stFileUploaderDropzone"] {{
    background: rgba(255,255,255,0.04);
    border: 1.5px dashed rgba(0,220,70,0.5);
    border-radius: 18px; padding: 1.5rem;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {GROWTH}; background: rgba(0,220,70,0.07);
}}
[data-testid="stFileUploaderDropzone"] * {{ color: #d7e3e1 !important; }}
[data-testid="stBaseButton-secondary"] {{
    color: {CHALKBOARD} !important; background: {GROWTH} !important;
    border: none !important; font-weight: 700 !important;
}}

/* ---- download buttons (CTA = Growth Green, all-caps) ---- */
.stDownloadButton button {{
    width: 100%;
    background: {GROWTH} !important;
    color: {CHALKBOARD} !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: .06em !important; text-transform: uppercase !important;
    font-size: .82rem !important;
    padding: .7rem 1rem !important;
    box-shadow: 0 8px 22px rgba(0,220,70,0.3) !important;
    transition: transform .12s ease, box-shadow .12s ease !important;
}}
.stDownloadButton button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(0,220,70,0.45) !important;
}}

/* expanders */
[data-testid="stExpander"] {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,220,70,0.18); border-radius: 12px;
}}

/* footer */
.brand-footer {{
    text-align: center; margin-top: 2rem; padding-top: 1.2rem;
    color: #8aa19f; font-family: 'Lora', serif; font-size: .9rem;
}}
.brand-footer a {{ color: {GROWTH}; text-decoration: none; font-weight: 600; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

logo_html = f'<img class="logo" src="{LOGO}" alt="Greatify" />' if LOGO else ""
st.markdown(
    f"""
    <div class="hero">
        {logo_html}
        <h1>File <span class="accent">ID</span> Renamer</h1>
        <p class="sub">Drop the names — keep the IDs. Clean numeric file names in one click.</p>
        <div class="accent-line"></div>
        <span class="chip">250701001-Abhilasha&nbsp;Jha.jpeg&nbsp;&nbsp;→&nbsp;&nbsp;250701001.jpeg</span>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Upload images or a zip file",
    accept_multiple_files=True,
    label_visibility="collapsed",
)


def render_rows(pairs: list[tuple[str, str]]) -> None:
    """Render old -> new rename rows as styled HTML."""
    html = ""
    for old, new in pairs:
        html += (
            f'<div class="row"><span class="old">{old}</span>'
            f'<span class="arrow">→</span><span class="new">{new}</span></div>'
        )
    st.markdown(html, unsafe_allow_html=True)


if uploaded_files:
    image_results = []   # (new_name, bytes) for loose images
    skipped = []         # original names with no ID
    used_names: dict[str, int] = {}

    total_renamed = 0
    total_skipped = 0
    total_zips = 0
    processed = []

    for uploaded in uploaded_files:
        is_zip = uploaded.name.lower().endswith(".zip") or zipfile.is_zipfile(
            io.BytesIO(uploaded.getvalue())
        )

        if is_zip:
            total_zips += 1
            try:
                zip_bytes, renamed, zskipped = rename_zip(uploaded.getvalue())
            except zipfile.BadZipFile:
                processed.append(("error", uploaded.name))
                continue
            total_renamed += len(renamed)
            total_skipped += len(zskipped)

            # Keep the SAME name as the uploaded zip; only the files inside
            # are renamed to their IDs.
            out_name = uploaded.name
            if not out_name.lower().endswith(".zip"):
                out_name += ".zip"
            processed.append(
                ("zip", uploaded.name, renamed, zskipped, zip_bytes, out_name)
            )
        else:
            target = new_name(uploaded.name)
            if target is None:
                skipped.append(uploaded.name)
                total_skipped += 1
                continue
            target = dedupe(target, used_names)
            image_results.append((target, uploaded.getvalue()))
            total_renamed += 1

    # ---- metrics bar ----
    st.markdown(
        f"""
        <div class="metrics">
            <div class="metric"><div class="num">{total_renamed}</div><div class="lbl">Renamed</div></div>
            <div class="metric"><div class="num">{total_zips}</div><div class="lbl">Zip files</div></div>
            <div class="metric"><div class="num">{total_skipped}</div><div class="lbl">Skipped</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- zip cards ----
    for item in processed:
        if item[0] == "error":
            st.error(f"`{item[1]}` is not a valid zip file.")
            continue
        if item[0] != "zip":
            continue
        _, zname, renamed, zskipped, zip_bytes, out_name = item

        st.markdown(
            f'<div class="card"><div class="card-title">📦 {zname}</div>',
            unsafe_allow_html=True,
        )
        if renamed:
            render_rows(renamed[:50])
            if len(renamed) > 50:
                st.caption(f"… and {len(renamed) - 50} more")
            st.download_button(
                label=f"⬇  Download {out_name}  ·  {len(renamed)} files",
                data=zip_bytes,
                file_name=out_name,
                mime="application/zip",
                key=f"dl-zip-{zname}",
            )
        else:
            st.warning("No files with a numeric ID were found in this zip.")
        if zskipped:
            with st.expander(f"⚠️ {len(zskipped)} file(s) left unchanged (no ID)"):
                for n in zskipped:
                    st.write(f"• {n}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- loose images card ----
    if image_results:
        st.markdown(
            '<div class="card"><div class="card-title">🖼️ Renamed images</div>',
            unsafe_allow_html=True,
        )
        render_rows([(t, t) for t, _ in image_results])

        if len(image_results) > 1:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for target, data in image_results:
                    zf.writestr(target, data)
            buffer.seek(0)
            st.download_button(
                label=f"⬇  Download all  ·  {len(image_results)} files",
                data=buffer,
                file_name="renamed_files.zip",
                mime="application/zip",
                key="dl-all-zip",
            )
        else:
            target, data = image_results[0]
            st.download_button(
                label=f"⬇  Download {target}",
                data=data,
                file_name=target,
                key=f"dl-{target}",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if skipped:
        with st.expander(f"⚠️ {len(skipped)} file(s) skipped (no numeric ID)"):
            for name in skipped:
                st.write(f"• {name}")
else:
    st.markdown(
        f"""
        <div class="card" style="text-align:center;">
            <div style="font-size:2.6rem; margin-bottom:.4rem;">📂</div>
            <div style="font-family:'Lora',serif; color:{CHALKBOARD};">
                Drag &amp; drop your <b>images</b> or a <b>.zip</b> above to get started.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="brand-footer">Making institutions <b style="color:#00DC46;">greater</b>'
    '&nbsp;·&nbsp;<a href="https://www.greatify.ai">www.greatify.ai</a></div>',
    unsafe_allow_html=True,
)
