"""
撮影シート生成アプリ  —  Streamlit版
────────────────────────────────────────
【起動方法（ローカル）】
  streamlit run app.py

【クラウド公開】
  Streamlit Community Cloud (share.streamlit.io) にデプロイ
────────────────────────────────────────
"""

import os
import tempfile
import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(
    page_title='撮影シート生成ツール',
    page_icon='📸',
    layout='centered',
)

# ────────────────────────────────────────
#  スタイル
# ────────────────────────────────────────
st.markdown("""
<style>
    .main-title  { font-size:1.8rem; font-weight:700; color:#1a3d6e; margin-bottom:0.2rem; }
    .sub-title   { font-size:0.95rem; color:#666; margin-bottom:1.5rem; }
    .section-hdr { font-size:1.05rem; font-weight:600; color:#1a3d6e;
                   border-left:4px solid #1a3d6e; padding-left:0.5rem; margin:1.2rem 0 0.5rem; }
    .info-box    { background:#eef3fb; border-radius:6px; padding:0.8rem 1rem;
                   font-size:0.85rem; color:#444; margin-bottom:0.8rem; }
    .success-box { background:#e8f5e9; border-radius:6px; padding:0.8rem 1rem;
                   font-size:0.9rem; color:#2e7d32; margin:0.5rem 0; }
    .warn-box    { background:#fff8e1; border-radius:6px; padding:0.8rem 1rem;
                   font-size:0.85rem; color:#795548; margin:0.5rem 0; }
    div[data-testid="stDownloadButton"] button {
        background-color:#1a3d6e; color:white; border-radius:6px;
        font-size:1rem; padding:0.6rem 1.2rem; width:100%;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────
#  ヘッダー
# ────────────────────────────────────────
st.markdown('<div class="main-title">📸 撮影シート生成ツール</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">ExcelとPDFをアップロードするだけで、A3横の撮影シートを自動生成します</div>',
    unsafe_allow_html=True)

# ────────────────────────────────────────
#  Step 1: Excel
# ────────────────────────────────────────
st.markdown('<div class="section-hdr">Step 1　Excelファイルをアップロード</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="info-box">📥 Googleスプレッドシートを'
    '<b>ファイル → ダウンロード → Microsoft Excel (.xlsx)</b>'
    'で保存してアップロードしてください。</div>',
    unsafe_allow_html=True)

excel_file = st.file_uploader('Excelファイル (.xlsx)', type=['xlsx'], key='excel')

df_loaded = None
if excel_file:
    try:
        df_preview = pd.read_excel(excel_file, header=0, dtype=str).fillna('')
        excel_file.seek(0)
        st.markdown(
            f'<div class="success-box">✅ 読み込み完了：{len(df_preview)} 行 / {len(df_preview.columns)} 列</div>',
            unsafe_allow_html=True)
        with st.expander('データプレビュー（先頭3行）'):
            st.dataframe(df_preview.head(3), use_container_width=True)
        df_loaded = df_preview
    except Exception as e:
        st.error(f'Excel読み込みエラー: {e}')

# ────────────────────────────────────────
#  Step 2: 参照PDF
# ────────────────────────────────────────
st.markdown('<div class="section-hdr">Step 2　参照PDFをアップロード（複数可）</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="info-box">📎 スプレッドシートのF列（PDF）に指定したPDFファイルをアップロードしてください。'
    'ファイル名が一致するものが左パネルに表示されます。'
    '未アップロードの場合は左パネルが空白になります。</div>',
    unsafe_allow_html=True)

pdf_files = st.file_uploader(
    'PDFファイル（複数可）', type=['pdf'],
    accept_multiple_files=True, key='pdfs')

if pdf_files:
    st.markdown(
        f'<div class="success-box">✅ {len(pdf_files)} ファイルをアップロード済み</div>',
        unsafe_allow_html=True)
    for f in pdf_files:
        st.caption(f'　　{f.name}')

# ────────────────────────────────────────
#  Step 3: タイトル設定
# ────────────────────────────────────────
st.markdown('<div class="section-hdr">Step 3　シートタイトルを設定</div>',
            unsafe_allow_html=True)

title_input = st.text_input(
    'シートタイトル（各ページ右上に表示）',
    value='教材カタログ vol.101 撮影シート',
)

# ────────────────────────────────────────
#  Step 4: フォント（任意）
# ────────────────────────────────────────
with st.expander('⚙️ フォント設定（任意） — Kinto Sans を使う場合'):
    st.markdown(
        '**Kinto Sans** フォントファイル (`KintoSans-Regular.ttf`) をアップロードすると'
        'フォントが適用されます。アップロードしない場合は内蔵フォントを使用します。\n\n'
        'ダウンロード先: https://github.com/ookamiinc/kinto'
    )
    font_file = st.file_uploader(
        'KintoSans-Regular.ttf', type=['ttf', 'otf'], key='font')
    if font_file:
        st.success(f'✅ {font_file.name} を受け取りました')

# ────────────────────────────────────────
#  生成ボタン
# ────────────────────────────────────────
st.markdown('---')

generate_btn = st.button(
    '　📄　撮影シートを生成する　',
    use_container_width=True,
    type='primary',
    disabled=(excel_file is None),
)

if generate_btn and excel_file:
    with st.spinner('生成中です。しばらくお待ちください…'):
        try:
            import convert_shooting_sheet as cs

            # タイトル設定
            cs.CATALOG_TITLE = title_input

            # ── フォント ──
            custom_font_path = None
            if font_file:
                tmp_font = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
                tmp_font.write(font_file.read())
                tmp_font.flush()
                custom_font_path = tmp_font.name

            font = cs.setup_font(custom_path=custom_font_path)

            # ── Excel を一時ファイルに保存 ──
            excel_file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_xl:
                tmp_xl.write(excel_file.read())
                tmp_xl_path = tmp_xl.name

            df = cs.load_excel(tmp_xl_path)

            # ── PDF を一時ディレクトリに保存 ──
            pdf_dir = tempfile.mkdtemp()
            for pf in (pdf_files or []):
                dest = os.path.join(pdf_dir, pf.name)
                with open(dest, 'wb') as out:
                    out.write(pf.read())

            # ── PDF 生成 ──
            output_path = os.path.join(tempfile.gettempdir(), '撮影シート_出力.pdf')
            cs.build_pdf(df, output_path, font, pdf_dir=pdf_dir)

            with open(output_path, 'rb') as f:
                pdf_bytes = f.read()

            # ── 結果表示 ──
            st.markdown(
                '<div class="success-box">✅ 生成完了！下のボタンからダウンロードしてください。</div>',
                unsafe_allow_html=True)

            fname = os.path.splitext(excel_file.name)[0]
            st.download_button(
                label='　⬇　撮影シート PDF をダウンロード　',
                data=pdf_bytes,
                file_name=f'{fname}_撮影シート.pdf',
                mime='application/pdf',
                use_container_width=True,
            )

            with st.expander(f'生成サマリー（全 {len(df)} ページ）'):
                for i, (_, row) in enumerate(df.iterrows()):
                    fn = cs.get(row, 'filename', '—')
                    pn = cs.get(row, 'product_name', '—')
                    st.caption(f'p.{i+1:02d}　{fn}　{pn}')

        except Exception as e:
            st.error(f'❌ エラーが発生しました: {e}')
            import traceback
            st.code(traceback.format_exc())

# ────────────────────────────────────────
#  フッター
# ────────────────────────────────────────
st.markdown('---')
st.caption('本ツールは社内利用を目的としています。アップロードしたデータはセッション終了後に削除されます。')
