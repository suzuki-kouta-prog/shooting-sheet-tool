"""
Shooting Sheet Maker — Streamlit
"""

import os
import tempfile
import streamlit as st

st.set_page_config(
    page_title='Shooting Sheet Maker',
    layout='centered',
    initial_sidebar_state='collapsed',
)

# ── ダーク/ライトモード ────────────────────────────────
if 'dark' not in st.session_state:
    st.session_state.dark = False

dark = st.session_state.dark

BG       = '#000000' if dark else '#ffffff'
FG       = '#ffffff' if dark else '#000000'
BORDER   = '#555555' if dark else '#000000'
HOVER    = '#1a1a1a' if dark else '#f2f2f2'
MUTED    = '#888888' if dark else '#999999'
DISABLED = '#444444' if dark else '#cccccc'
INPUT_BG = '#111111' if dark else '#fafafa'

st.markdown(f"""
<style>
/* ════ 全画面背景 ════ */
html, body {{
  margin: 0; padding: 0;
  background: {BG} !important;
  min-height: 100vh;
}}
.stApp,
.stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"],
.main, section.main {{
  background: {BG} !important;
  min-height: 100vh;
}}
[data-testid="stVerticalBlock"] {{
  background: {BG} !important;
  gap: 0.6rem !important;        /* ← 要素間の縦余白を圧縮 */
}}

/* ════ コンテンツ幅・パディング ════ */
.block-container {{
  max-width: 620px !important;
  padding: 1.6rem 1.5rem 2rem !important;
  background: {BG} !important;
}}

/* ════ 全体フォント・色 ════ */
html, body, [class*="css"], p, div, span, label {{
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
  color: {FG};
}}

/* ════ タイトル ════ */
.ssm-title {{
  text-align: center;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: {FG};
  margin: 0 0 1.4rem 0;
}}

/* ════ ラベル ════ */
.ssm-label {{
  font-size: 0.82rem;
  font-weight: 500;
  color: {FG};
  margin-bottom: 0.3rem;
  display: block;
}}

/* ════ アップローダー ════ */
/* Streamlit の "Browse files" ボタンと説明テキストを非表示 */
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {{
  display: none !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] {{
  padding: 0 !important;
  margin: 0 !important;
}}
/* Browse files ボタン非表示（ゾーン全体がクリック可能） */
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {{
  display: none !important;
}}
/* ドロップゾーン本体 */
[data-testid="stFileUploader"] > label {{ display: none !important; }}
[data-testid="stFileUploaderDropzone"] {{
  border: 1.5px solid {BORDER} !important;
  border-radius: 14px !important;
  background: {INPUT_BG} !important;
  min-height: 80px !important;
  max-height: 80px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer;
  transition: background 0.2s;
  overflow: hidden;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  background: {HOVER} !important;
}}
/* アップロードアイコン */
[data-testid="stFileUploaderDropzoneInstructions"] svg {{
  width: 22px !important;
  height: 22px !important;
  fill: {FG} !important;
  stroke: {FG} !important;
  opacity: 0.6;
}}
/* アップロード済みファイル名 */
[data-testid="stFileUploaderFileName"] {{
  font-size: 0.75rem !important;
  color: {MUTED} !important;
}}
/* アップローダー全体の外側余白を削除 */
[data-testid="stFileUploader"] {{
  margin-bottom: 0 !important;
}}

/* ════ テキスト入力 ════ */
[data-testid="stTextInput"] > label {{ display: none !important; }}
[data-testid="stTextInput"] input {{
  border: 1.5px solid {BORDER} !important;
  border-radius: 12px !important;
  background: {INPUT_BG} !important;
  color: {FG} !important;
  font-size: 0.92rem !important;
  padding: 0.55rem 0.9rem !important;
  box-shadow: none !important;
}}
[data-testid="stTextInput"] input:focus {{
  background: {HOVER} !important;
  box-shadow: none !important;
  outline: none !important;
}}

/* ════ ボタン共通 ════ */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button {{
  width: 100% !important;
  background: {BG} !important;
  color: {FG} !important;
  border: 1.5px solid {BORDER} !important;
  border-radius: 12px !important;
  font-size: 0.92rem !important;
  font-weight: 500 !important;
  padding: 0.6rem 1rem !important;
  box-shadow: none !important;
  transition: background 0.2s;
}}
[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {{
  background: {HOVER} !important;
  border-color: {BORDER} !important;
}}
[data-testid="stButton"] > button:disabled {{
  border-color: {DISABLED} !important;
  color: {DISABLED} !important;
  background: {BG} !important;
}}

/* トグルボタン（小） */
button[kind="secondary"][data-testid="stButton"] > button {{
  padding: 0.25rem 0.6rem !important;
  font-size: 0.75rem !important;
  border-radius: 20px !important;
  border: 1px solid {BORDER} !important;
  color: {MUTED} !important;
  width: auto !important;
}}

/* ════ spinner ════ */
[data-testid="stSpinner"] > div {{ border-top-color: {FG} !important; }}

/* ════ 余分なUI非表示 ════ */
#MainMenu, footer, header {{ visibility: hidden; }}

/* カラム間ギャップ */
[data-testid="stHorizontalBlock"] {{
  gap: 1rem !important;
  align-items: flex-start !important;
}}
</style>
""", unsafe_allow_html=True)


# ── モード切り替えトグル（右上） ──────────────────────
t_col = st.columns([8, 1])[1]
with t_col:
    icon = '☀️' if dark else '🌙'
    if st.button(icon, key='toggle'):
        st.session_state.dark = not st.session_state.dark
        st.rerun()

# ── タイトル ──────────────────────────────────────────
st.markdown('<div class="ssm-title">Shooting Sheet Maker</div>',
            unsafe_allow_html=True)

# ── 1. Excel ／ 2. PDF（2カラム）────────────────────
col1, col2 = st.columns(2, gap='small')

with col1:
    st.markdown('<span class="ssm-label">1. Excel upload</span>',
                unsafe_allow_html=True)
    excel_file = st.file_uploader(
        '_', type=['xlsx'], key='excel', label_visibility='collapsed')

with col2:
    st.markdown('<span class="ssm-label">2. PDF upload</span>',
                unsafe_allow_html=True)
    pdf_files = st.file_uploader(
        '_', type=['pdf'], accept_multiple_files=True,
        key='pdfs', label_visibility='collapsed')

# ── 3. File Name ──────────────────────────────────────
st.markdown('<span class="ssm-label">3. File Name</span>',
            unsafe_allow_html=True)
title_input = st.text_input(
    '_', value='教材カタログ vol.101 撮影シート',
    label_visibility='collapsed')

# ── Convert to PDF ────────────────────────────────────
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'pdf_fname' not in st.session_state:
    st.session_state.pdf_fname = '撮影シート.pdf'

if st.button('Convert to PDF', disabled=(excel_file is None),
             use_container_width=True):
    with st.spinner(''):
        try:
            import convert_shooting_sheet as cs
            cs.CATALOG_TITLE = title_input
            font = cs.setup_font()

            excel_file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                f.write(excel_file.read())
                tmp_xl = f.name

            df = cs.load_excel(tmp_xl)

            pdf_dir = tempfile.mkdtemp()
            for pf in (pdf_files or []):
                with open(os.path.join(pdf_dir, pf.name), 'wb') as f:
                    f.write(pf.read())

            out = os.path.join(tempfile.gettempdir(), 'output.pdf')
            cs.build_pdf(df, out, font, pdf_dir=pdf_dir)

            with open(out, 'rb') as f:
                st.session_state.pdf_bytes = f.read()
            st.session_state.pdf_fname = (
                os.path.splitext(excel_file.name)[0] + '_撮影シート.pdf')

        except Exception as e:
            st.error(str(e))
            import traceback; st.code(traceback.format_exc())

if st.session_state.pdf_bytes:
    st.download_button(
        '↓  Download',
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.pdf_fname,
        mime='application/pdf',
        use_container_width=True,
    )
