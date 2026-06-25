"""
撮影シート生成アプリ — Streamlit版（Mac風クリーンUI）
"""

import os
import tempfile
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='撮影シート生成ツール',
    page_icon='📷',
    layout='centered',
    initial_sidebar_state='collapsed',
)

# ── Apple風 グローバルCSS ──────────────────────────────────────────
st.markdown("""
<style>
  /* ベースフォント・背景 */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                 'Inter', 'Helvetica Neue', Arial, sans-serif;
    background-color: #f5f5f7;
    color: #1d1d1f;
  }

  /* ページ全体の余白 */
  .block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
    max-width: 680px;
  }

  /* ヘッダー */
  .app-header { text-align: center; margin-bottom: 2.5rem; }
  .app-icon   { font-size: 2.8rem; margin-bottom: 0.4rem; }
  .app-title  { font-size: 1.9rem; font-weight: 600;
                color: #1d1d1f; letter-spacing: -0.5px; margin: 0; }
  .app-sub    { font-size: 0.95rem; color: #86868b;
                font-weight: 400; margin-top: 0.3rem; }

  /* カードコンテナ */
  .card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04);
  }

  /* ステップラベル */
  .step-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #0071e3;
    margin-bottom: 0.3rem;
  }
  .step-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #1d1d1f;
    margin-bottom: 0.8rem;
  }

  /* ヒントテキスト */
  .hint {
    font-size: 0.82rem;
    color: #86868b;
    margin-top: 0.5rem;
    line-height: 1.5;
  }

  /* 成功バナー */
  .success-banner {
    background: #f0faf0;
    border: 1px solid #c3e6c3;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    font-size: 0.88rem;
    color: #1a6e1a;
    margin-top: 0.6rem;
  }

  /* ファイルアップローダーのラベル非表示 */
  [data-testid="stFileUploaderDropzoneInstructions"] {
    font-size: 0.85rem;
    color: #86868b;
  }

  /* アップロードゾーン */
  [data-testid="stFileUploader"] section {
    border: 1.5px dashed #d2d2d7 !important;
    border-radius: 12px !important;
    background: #fafafa !important;
    padding: 1rem !important;
  }
  [data-testid="stFileUploader"] section:hover {
    border-color: #0071e3 !important;
    background: #f0f6ff !important;
  }

  /* テキスト入力 */
  [data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1.5px solid #d2d2d7 !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 0.8rem !important;
    background: #fafafa !important;
    color: #1d1d1f !important;
    transition: border-color 0.15s;
  }
  [data-testid="stTextInput"] input:focus {
    border-color: #0071e3 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(0,113,227,0.12) !important;
  }

  /* プライマリボタン */
  [data-testid="stButton"] > button[kind="primary"] {
    background: #0071e3 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 980px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    transition: background 0.15s, transform 0.1s;
    letter-spacing: -0.01em;
  }
  [data-testid="stButton"] > button[kind="primary"]:hover {
    background: #0077ed !important;
    transform: scale(1.01);
  }
  [data-testid="stButton"] > button[kind="primary"]:disabled {
    background: #d2d2d7 !important;
    color: #a0a0a5 !important;
  }

  /* ダウンロードボタン */
  [data-testid="stDownloadButton"] > button {
    background: #1d1d1f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 980px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    transition: background 0.15s;
  }
  [data-testid="stDownloadButton"] > button:hover {
    background: #3d3d3f !important;
  }

  /* expander */
  [data-testid="stExpander"] {
    border: 1px solid #e0e0e5 !important;
    border-radius: 12px !important;
    background: #fafafa !important;
  }
  [data-testid="stExpander"] summary {
    font-size: 0.88rem !important;
    color: #555 !important;
    padding: 0.6rem 0.8rem !important;
  }

  /* divider */
  hr { border: none; border-top: 1px solid #e0e0e5; margin: 1.5rem 0; }

  /* フッター */
  .footer {
    text-align: center;
    font-size: 0.78rem;
    color: #b0b0b5;
    margin-top: 2rem;
  }

  /* Streamlitデフォルト要素を隠す */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── ヘッダー ──────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-icon">📷</div>
  <div class="app-title">撮影シート生成ツール</div>
  <div class="app-sub">ExcelとPDFをアップロードするだけで撮影シートを自動生成します</div>
</div>
""", unsafe_allow_html=True)


# ── Step 1: Excel ─────────────────────────────────────────────────
st.markdown("""
<div class="card">
  <div class="step-label">Step 1</div>
  <div class="step-title">Excelファイルをアップロード</div>
</div>
""", unsafe_allow_html=True)

excel_file = st.file_uploader(
    'Googleスプレッドシートを .xlsx でダウンロードしてアップロード',
    type=['xlsx'], label_visibility='collapsed', key='excel')

if excel_file:
    try:
        df_preview = pd.read_excel(excel_file, header=0, dtype=str).fillna('')
        excel_file.seek(0)
        st.markdown(
            f'<div class="success-banner">✓　{len(df_preview)} 行 / {len(df_preview.columns)} 列を読み込みました</div>',
            unsafe_allow_html=True)
        with st.expander('データを確認する'):
            st.dataframe(df_preview.head(5), use_container_width=True,
                         hide_index=True)
    except Exception as e:
        st.error(f'読み込みエラー: {e}')

st.markdown('<p class="hint">ファイル → ダウンロード → Microsoft Excel (.xlsx)</p>',
            unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)


# ── Step 2: PDF ───────────────────────────────────────────────────
st.markdown("""
<div class="card">
  <div class="step-label">Step 2</div>
  <div class="step-title">参照PDFをアップロード</div>
</div>
""", unsafe_allow_html=True)

pdf_files = st.file_uploader(
    'スプレッドシートのF列に指定したPDFファイル（複数可）',
    type=['pdf'], accept_multiple_files=True,
    label_visibility='collapsed', key='pdfs')

if pdf_files:
    st.markdown(
        f'<div class="success-banner">✓　{len(pdf_files)} ファイルをアップロードしました</div>',
        unsafe_allow_html=True)
    with st.expander('ファイル一覧を確認する'):
        for f in pdf_files:
            st.caption(f'　{f.name}')

st.markdown(
    '<p class="hint">F列のパス末尾のファイル名と一致するPDFが左パネルに表示されます。<br>'
    '未アップロードの場合は左パネルが空白になります。</p>',
    unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)


# ── Step 3: タイトル ──────────────────────────────────────────────
st.markdown("""
<div class="card">
  <div class="step-label">Step 3</div>
  <div class="step-title">シートタイトルを設定</div>
</div>
""", unsafe_allow_html=True)

title_input = st.text_input(
    'タイトル', value='教材カタログ vol.101 撮影シート',
    label_visibility='collapsed')

st.markdown('<hr>', unsafe_allow_html=True)


# ── Step 4: フォント（任意）──────────────────────────────────────
with st.expander('⚙️　フォント設定（任意）'):
    st.markdown(
        '<p class="hint">Kinto Sans フォントファイル (KintoSans-Regular.ttf) を'
        'アップロードするとフォントが適用されます。<br>'
        'ダウンロード先: github.com/ookamiinc/kinto</p>',
        unsafe_allow_html=True)
    font_file = st.file_uploader(
        'KintoSans-Regular.ttf', type=['ttf', 'otf'], key='font',
        label_visibility='collapsed')
    if font_file:
        st.markdown(
            f'<div class="success-banner">✓　{font_file.name} を受け取りました</div>',
            unsafe_allow_html=True)


# ── 生成ボタン ────────────────────────────────────────────────────
st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

generate_btn = st.button(
    '撮影シートを生成する',
    type='primary',
    disabled=(excel_file is None),
    use_container_width=True,
)

if generate_btn and excel_file:
    with st.spinner('生成しています…'):
        try:
            import convert_shooting_sheet as cs

            cs.CATALOG_TITLE = title_input

            # フォント
            custom_font_path = None
            if font_file:
                tmp_font = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
                tmp_font.write(font_file.read())
                tmp_font.flush()
                custom_font_path = tmp_font.name

            font = cs.setup_font(custom_path=custom_font_path)

            # Excel
            excel_file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_xl:
                tmp_xl.write(excel_file.read())
                tmp_xl_path = tmp_xl.name

            df = cs.load_excel(tmp_xl_path)

            # PDF保存先
            pdf_dir = tempfile.mkdtemp()
            for pf in (pdf_files or []):
                dest = os.path.join(pdf_dir, pf.name)
                with open(dest, 'wb') as out:
                    out.write(pf.read())

            # 生成
            output_path = os.path.join(tempfile.gettempdir(), '撮影シート_出力.pdf')
            cs.build_pdf(df, output_path, font, pdf_dir=pdf_dir)

            with open(output_path, 'rb') as f:
                pdf_bytes = f.read()

            # 完了
            st.markdown("""
<div style="background:#f0faf0; border:1px solid #c3e6c3; border-radius:14px;
     padding:1.2rem 1.4rem; text-align:center; margin:0.8rem 0;">
  <div style="font-size:1.5rem; margin-bottom:0.3rem;">✓</div>
  <div style="font-weight:600; color:#1a6e1a; font-size:0.95rem;">生成が完了しました</div>
</div>
""", unsafe_allow_html=True)

            fname = os.path.splitext(excel_file.name)[0]
            st.download_button(
                label='PDFをダウンロード',
                data=pdf_bytes,
                file_name=f'{fname}_撮影シート.pdf',
                mime='application/pdf',
                use_container_width=True,
            )

            with st.expander(f'生成内容　{len(df)} ページ'):
                for i, (_, row) in enumerate(df.iterrows()):
                    fn = cs.get(row, 'filename', '—')
                    pn = cs.get(row, 'product_name', '—')
                    st.caption(f'p.{i+1:02d}　{fn}　　{pn}')

        except Exception as e:
            st.error(f'エラーが発生しました: {e}')
            import traceback
            st.code(traceback.format_exc(), language='python')


# ── フッター ──────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">アップロードされたデータはセッション終了後に削除されます</div>',
    unsafe_allow_html=True)
