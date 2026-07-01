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

st.markdown("""
<style>
  /* ── ベース ── */
  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue',
                 Arial, sans-serif;
    background: #ffffff;
    color: #000000;
  }
  .block-container {
    max-width: 660px;
    padding: 5rem 1.5rem 4rem;
  }

  /* ── タイトル ── */
  .title {
    text-align: center;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 3rem;
    color: #000;
  }

  /* ── セクションラベル ── */
  .label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #000;
    margin-bottom: 0.5rem;
  }

  /* ── アップロードゾーン ── */
  [data-testid="stFileUploader"] > label { display: none !important; }
  [data-testid="stFileUploaderDropzone"] {
    border: 1.5px solid #000 !important;
    border-radius: 14px !important;
    background: #fff !important;
    min-height: 130px !important;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
  }
  [data-testid="stFileUploaderDropzone"]:hover {
    background: #f7f7f7 !important;
  }
  [data-testid="stFileUploaderDropzoneInstructions"] {
    color: #000 !important;
    font-size: 0.82rem !important;
  }
  [data-testid="stFileUploaderDropzoneInstructions"] svg {
    fill: #000 !important;
    stroke: #000 !important;
  }

  /* アップロード済みファイル名 */
  [data-testid="stFileUploaderFileName"] {
    font-size: 0.8rem !important;
    color: #333 !important;
  }

  /* ── テキスト入力 ── */
  [data-testid="stTextInput"] > label { display: none !important; }
  [data-testid="stTextInput"] input {
    border: 1.5px solid #000 !important;
    border-radius: 12px !important;
    background: #fff !important;
    color: #000 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
    box-shadow: none !important;
    transition: background 0.15s;
  }
  [data-testid="stTextInput"] input:focus {
    background: #f7f7f7 !important;
    outline: none !important;
    box-shadow: none !important;
  }

  /* ── ボタン（生成 & ダウンロード共通） ── */
  [data-testid="stButton"] > button,
  [data-testid="stDownloadButton"] > button {
    width: 100% !important;
    background: #fff !important;
    color: #000 !important;
    border: 1.5px solid #000 !important;
    border-radius: 12px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    letter-spacing: 0.01em;
    transition: background 0.15s;
    box-shadow: none !important;
  }
  [data-testid="stButton"] > button:hover,
  [data-testid="stDownloadButton"] > button:hover {
    background: #f0f0f0 !important;
    border-color: #000 !important;
  }
  [data-testid="stButton"] > button:disabled {
    border-color: #ccc !important;
    color: #ccc !important;
  }

  /* ── spinner ── */
  [data-testid="stSpinner"] > div {
    border-top-color: #000 !important;
  }

  /* ── 余分なUI非表示 ── */
  #MainMenu, footer, header { visibility: hidden; }

  /* 区切り余白 */
  .gap { margin-top: 1.8rem; }
  .gap-sm { margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── タイトル ──────────────────────────────────────────
st.markdown('<div class="title">Shooting Sheet Maker</div>',
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


# ── File download ─────────────────────────────────────
st.markdown('<div class="gap"></div>', unsafe_allow_html=True)

# 生成済みPDFをセッションに保持
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'pdf_fname' not in st.session_state:
    st.session_state.pdf_fname = '撮影シート.pdf'

# ExcelがアップされていればOK → クリックで生成
btn_clicked = st.button(
    'File download',
    disabled=(excel_file is None),
    use_container_width=True,
)

if btn_clicked and excel_file:
    with st.spinner(''):
        try:
            import convert_shooting_sheet as cs

            cs.CATALOG_TITLE = title_input

            # フォント（Kinto Sans を自動検索、なければ内蔵フォント）
            font = cs.setup_font()

            # Excel を一時保存
            excel_file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                tmp.write(excel_file.read())
                tmp_xl = tmp.name

            df = cs.load_excel(tmp_xl)

            # PDF を一時ディレクトリに保存
            pdf_dir = tempfile.mkdtemp()
            for pf in (pdf_files or []):
                with open(os.path.join(pdf_dir, pf.name), 'wb') as f:
                    f.write(pf.read())

            # 撮影シート生成
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

# 生成済みならダウンロードボタンに切り替え
if st.session_state.pdf_bytes:
    st.markdown('<div class="gap-sm"></div>', unsafe_allow_html=True)
    st.download_button(
        label='↓  ダウンロード',
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.pdf_fname,
        mime='application/pdf',
        use_container_width=True,
    )
