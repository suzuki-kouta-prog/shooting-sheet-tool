"""
Shooting Sheet Maker — Streamlit
"""

import os
import tempfile
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='Shooting Sheet Maker',
    layout='centered',
    initial_sidebar_state='collapsed',
)

# ── ダーク/ライトモード状態管理 ───────────────────────
if 'dark' not in st.session_state:
    st.session_state.dark = False

dark = st.session_state.dark

# モードに応じた色定義
BG      = '#000000' if dark else '#ffffff'
FG      = '#ffffff' if dark else '#000000'
BORDER  = '#444444' if dark else '#000000'
HOVER   = '#1a1a1a' if dark else '#f0f0f0'
MUTED   = '#888888' if dark else '#999999'
DISABLED= '#444444' if dark else '#cccccc'
INPUT_BG= '#111111' if dark else '#ffffff'
INPUT_HV= '#1a1a1a' if dark else '#f7f7f7'

st.markdown(f"""
<style>
  /* ── ベース：ブラウザ全体を背景色で埋める ── */
  html {{
    height: 100%;
    background: {BG} !important;
  }}
  body {{
    min-height: 100vh;
    background: {BG} !important;
  }}
  html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue',
                 Arial, sans-serif;
    color: {FG};
  }}
  /* Streamlit の全ラッパーを背景で統一 */
  .stApp,
  .stApp > div,
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewBlockContainer"],
  [data-testid="stVerticalBlock"],
  [data-testid="stMainBlockContainer"],
  .main,
  section.main {{
    background: {BG} !important;
    min-height: 100vh;
  }}
  .block-container {{
    max-width: 660px;
    padding: 4rem 1.5rem 4rem;
    background: {BG} !important;
  }}

  /* ── タイトル ── */
  .title {{
    text-align: center;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 3rem;
    color: {FG};
  }}

  /* ── セクションラベル ── */
  .label {{
    font-size: 0.85rem;
    font-weight: 500;
    color: {FG};
    margin-bottom: 0.5rem;
  }}

  /* ── モード切り替えトグル ── */
  .mode-toggle {{
    text-align: right;
    margin-bottom: 2rem;
  }}

  /* ── アップロードゾーン ── */
  [data-testid="stFileUploader"] > label {{ display: none !important; }}
  [data-testid="stFileUploaderDropzone"] {{
    border: 1.5px solid {BORDER} !important;
    border-radius: 14px !important;
    background: {INPUT_BG} !important;
    min-height: 130px !important;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  }}
  [data-testid="stFileUploaderDropzone"]:hover {{
    background: {INPUT_HV} !important;
  }}
  [data-testid="stFileUploaderDropzoneInstructions"] {{
    color: {FG} !important;
    font-size: 0.82rem !important;
  }}
  [data-testid="stFileUploaderDropzoneInstructions"] svg {{
    fill: {FG} !important;
    stroke: {FG} !important;
  }}
  [data-testid="stFileUploaderFileName"] {{
    font-size: 0.8rem !important;
    color: {MUTED} !important;
  }}

  /* ── テキスト入力 ── */
  [data-testid="stTextInput"] > label {{ display: none !important; }}
  [data-testid="stTextInput"] input {{
    border: 1.5px solid {BORDER} !important;
    border-radius: 12px !important;
    background: {INPUT_BG} !important;
    color: {FG} !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
    box-shadow: none !important;
    transition: background 0.2s;
  }}
  [data-testid="stTextInput"] input:focus {{
    background: {INPUT_HV} !important;
    outline: none !important;
    box-shadow: none !important;
  }}

  /* ── ボタン共通 ── */
  [data-testid="stButton"] > button,
  [data-testid="stDownloadButton"] > button {{
    width: 100% !important;
    background: {BG} !important;
    color: {FG} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 12px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    letter-spacing: 0.01em;
    transition: background 0.2s;
    box-shadow: none !important;
  }}
  [data-testid="stButton"] > button:hover,
  [data-testid="stDownloadButton"] > button:hover {{
    background: {HOVER} !important;
    border-color: {BORDER} !important;
  }}
  [data-testid="stButton"] > button:disabled {{
    border-color: {DISABLED} !important;
    color: {DISABLED} !important;
  }}

  /* ── トグルボタン（小さめ） ── */
  [data-testid="stButton"].toggle-btn > button {{
    width: auto !important;
    padding: 0.3rem 0.8rem !important;
    font-size: 0.78rem !important;
    border-radius: 20px !important;
    border: 1px solid {BORDER} !important;
    color: {MUTED} !important;
  }}

  /* ── spinner ── */
  [data-testid="stSpinner"] > div {{
    border-top-color: {FG} !important;
  }}

  /* ── error ── */
  [data-testid="stAlert"] {{
    background: {'#1a0000' if dark else '#fff0f0'} !important;
    color: {'#ff6b6b' if dark else '#cc0000'} !important;
    border-color: {'#440000' if dark else '#ffcccc'} !important;
    border-radius: 12px !important;
  }}

  /* ── 余分なUI非表示 ── */
  #MainMenu, footer, header {{ visibility: hidden; }}

  .gap    {{ margin-top: 1.8rem; }}
  .gap-sm {{ margin-top: 1rem; }}
</style>
""", unsafe_allow_html=True)


# ── モード切り替えトグル（右上） ──────────────────────
toggle_col = st.columns([5, 1])[1]
with toggle_col:
    icon = '☀️' if dark else '🌙'
    if st.button(icon, key='mode_toggle', help='ダーク/ライト切り替え'):
        st.session_state.dark = not st.session_state.dark
        st.rerun()


# ── タイトル ──────────────────────────────────────────
st.markdown(f'<div class="title">Shooting Sheet Maker</div>',
            unsafe_allow_html=True)


# ── 1. Excel ／ 2. PDF（2カラム）────────────────────
col1, col2 = st.columns(2, gap='medium')

with col1:
    st.markdown('<div class="label">1. Excel upload</div>',
                unsafe_allow_html=True)
    excel_file = st.file_uploader(
        'excel', type=['xlsx'], key='excel', label_visibility='collapsed')

with col2:
    st.markdown('<div class="label">2. PDF upload</div>',
                unsafe_allow_html=True)
    pdf_files = st.file_uploader(
        'pdf', type=['pdf'], accept_multiple_files=True,
        key='pdfs', label_visibility='collapsed')


# ── 3. File Name ──────────────────────────────────────
st.markdown('<div class="gap"></div>', unsafe_allow_html=True)
st.markdown('<div class="label">3. File Name</div>', unsafe_allow_html=True)
title_input = st.text_input(
    'title', value='教材カタログ vol.101 撮影シート',
    label_visibility='collapsed')


# ── Convert to PDF ────────────────────────────────────
st.markdown('<div class="gap"></div>', unsafe_allow_html=True)

if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'pdf_fname' not in st.session_state:
    st.session_state.pdf_fname = '撮影シート.pdf'

btn_clicked = st.button(
    'Convert to PDF',
    disabled=(excel_file is None),
    use_container_width=True,
)

if btn_clicked and excel_file:
    with st.spinner(''):
        try:
            import convert_shooting_sheet as cs

            cs.CATALOG_TITLE = title_input
            font = cs.setup_font()

            excel_file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                tmp.write(excel_file.read())
                tmp_xl = tmp.name

            df = cs.load_excel(tmp_xl)

            pdf_dir = tempfile.mkdtemp()
            for pf in (pdf_files or []):
                with open(os.path.join(pdf_dir, pf.name), 'wb') as f:
                    f.write(pf.read())

            out_path = os.path.join(tempfile.gettempdir(), 'output.pdf')
            cs.build_pdf(df, out_path, font, pdf_dir=pdf_dir)

            with open(out_path, 'rb') as f:
                st.session_state.pdf_bytes = f.read()

            fname = os.path.splitext(excel_file.name)[0]
            st.session_state.pdf_fname = f'{fname}_撮影シート.pdf'

        except Exception as e:
            st.error(str(e))
            import traceback
            st.code(traceback.format_exc())

# 生成済みならダウンロードボタンを表示
if st.session_state.pdf_bytes:
    st.markdown('<div class="gap-sm"></div>', unsafe_allow_html=True)
    st.download_button(
        label='↓  Download',
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.pdf_fname,
        mime='application/pdf',
        use_container_width=True,
    )
