#!/usr/bin/env python3
"""
撮影シート変換スクリプト  v7.0
────────────────────────────────────────────────────
出力形式  : A3 横 (420mm × 297mm)
ページ単位: 1行 = 1ページ（ファイル名ごと）
左パネル  : 指定PDFをA4縦比率で表示（パス未指定は空白）
右パネル  : シンプル罫線フォーム（見本準拠）

【設定】
  CATALOG_TITLE : ヘッダータイトル
  FONT_PATHS    : Kinto Sansフォントの検索パス（順に試みる）

【使用方法（スタンドアロン）】
  python convert_shooting_sheet.py 入力.xlsx [出力.pdf]
────────────────────────────────────────────────────
"""

import sys, os, tempfile
from datetime import datetime
import pandas as pd
import fitz
from PIL import Image

from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Frame, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ════════════════════════════════════════════════════
#  設定
# ════════════════════════════════════════════════════
CATALOG_TITLE = '教材カタログ vol.101 撮影シート'

# Kinto Sans フォントの検索パス（Macの一般的な場所＋カレントディレクトリ）
FONT_PATHS = [
    './KintoSans-Regular.ttf',
    './fonts/KintoSans-Regular.ttf',
    os.path.expanduser('~/Library/Fonts/KintoSans-Regular.ttf'),
    '/Library/Fonts/KintoSans-Regular.ttf',
    '/System/Library/Fonts/KintoSans-Regular.ttf',
]

# ════════════════════════════════════════════════════
#  ページサイズ・レイアウト
# ════════════════════════════════════════════════════
PAGE_W, PAGE_H = landscape(A3)
MARGIN   = 10 * mm
PANEL_H  = PAGE_H - 2 * MARGIN
LEFT_W   = PANEL_H * (210 / 297)   # A4縦比率
DIVIDER  = 6  * mm
RIGHT_X  = MARGIN + LEFT_W + DIVIDER
RIGHT_W  = PAGE_W - MARGIN - RIGHT_X

C_BLACK  = colors.black
C_WHITE  = colors.white
C_LABEL  = colors.HexColor('#e8e8e8')
C_BORDER = colors.HexColor('#aaaaaa')
C_DGRAY  = colors.HexColor('#333333')

# ════════════════════════════════════════════════════
#  フォント設定
# ════════════════════════════════════════════════════
_FONT_NAME   = 'KintoSans'
_FONT_LOADED = False

def setup_font(custom_path=None):
    """
    Kinto Sans TTFを検索して登録。
    見つからない場合は HeiseiKakuGo-W5 (CID) を使用。
    custom_path: Streamlit アプリがアップロードされたフォントパスを渡す場合に使用
    """
    global _FONT_NAME, _FONT_LOADED

    search_paths = ([custom_path] if custom_path else []) + FONT_PATHS

    for path in search_paths:
        if path and os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('KintoSans', path))
                _FONT_NAME   = 'KintoSans'
                _FONT_LOADED = True
                print(f'✅ フォント: Kinto Sans ({path})')
                return 'KintoSans'
            except Exception as e:
                print(f'⚠ フォント読み込み失敗 ({path}): {e}')

    # フォールバック
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    _FONT_NAME   = 'HeiseiKakuGo-W5'
    _FONT_LOADED = True
    print('⚠ Kinto Sans未検出 → HeiseiKakuGo-W5 を使用')
    return 'HeiseiKakuGo-W5'

# ════════════════════════════════════════════════════
#  列定義
# ════════════════════════════════════════════════════
COL_NAMES = [
    'date',          # 0  A 撮影日時
    'studio',        # 1  B スタジオ
    'time',          # 2  C 撮影時間
    'subject',       # 3  D 教科
    'pub_page',      # 4  E 掲載頁
    'pdf_path',      # 5  F PDFファイルパス
    'product_name',  # 6  G 商品名
    'product_num',   # 7  H 型番
    'client',        # 8  I お客様担当
    'fn_ky',         # 9  J 撮影ナンバー(KY) ← グループキー①
    'fn_num',        # 10 K 番号              ← グループキー②
    'fn_branch',     # 11 L 枝番
    'filename',      # 12 M ファイル名(結合)
    'cut_type',      # 13 N カット内容
    'cnt_single',    # 14 O カット数(単品)     → 単品撮影欄
    'cnt_model',     # 15 P カット数(モデル)   → モデル撮影欄
    'cnt_image',     # 16 Q カット数(イメージ) → イメージ撮影欄
    'cnt_feature',   # 17 R カット数(特徴)     → 特徴欄
    'mdl_child',     # 18 S 児童・生徒モデル
    'mdl_teacher',   # 19 T 先生モデル
    'mdl_adult',     # 20 U 大人モデル
    'mdl_name',      # 21 V モデル名           → モデル名欄
    'background',    # 22 W 建て込みか白背景か
    'equipment',     # 23 X 必要備品
    'remarks',       # 24 Y 備考
]

def load_excel(path):
    df = pd.read_excel(path, header=0, dtype=str).fillna('')
    rename = {old: new for old, new in zip(df.columns, COL_NAMES[:len(df.columns)])}
    return df.rename(columns=rename)

def get(row, field, default=''):
    if field in row.index:
        v = str(row[field]).strip()
        return v if v not in ('', 'nan', 'None') else default
    return default

# ════════════════════════════════════════════════════
#  ユーティリティ
# ════════════════════════════════════════════════════
def format_date(date_str):
    """'2026/07/01' → '7月1日'"""
    for fmt in ('%Y/%m/%d', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return f'{dt.month}月{dt.day}日'
        except Exception:
            pass
    return date_str  # パース失敗時はそのまま

def get_shoot_numbers(df, row):
    """
    同じ J列(fn_ky) × K列(fn_num) を持つ全行の M列(filename) を取得し
    「／」で連結して返す。
    例: J=KY, K=1 のとき "KY-1-1／KY-1-2／KY-1-3"
    """
    ky  = get(row, 'fn_ky')
    num = get(row, 'fn_num')
    if not ky and not num:
        return get(row, 'filename')
    mask = (df['fn_ky'] == ky) & (df['fn_num'] == num)
    filenames = df.loc[mask, 'filename'].tolist()
    return '／'.join(f for f in filenames if f)

# ════════════════════════════════════════════════════
#  スタイルヘルパー
# ════════════════════════════════════════════════════
def ps(font, size, color=C_BLACK, align='left', leading=None):
    return ParagraphStyle(
        'x', fontName=font, fontSize=size, textColor=color,
        alignment={'left': 0, 'center': 1, 'right': 2}.get(align, 0),
        wordWrap='CJK', leading=leading or max(size * 1.45, size + 3),
    )

def P(text, font, size, color=C_BLACK, align='left'):
    return Paragraph(str(text) if text else '', ps(font, size, color, align))

# ════════════════════════════════════════════════════
#  左パネル: PDF描画
# ════════════════════════════════════════════════════
def render_left(c, pdf_path, tmp_dir, font):
    lx, ly, lw, lh = MARGIN, MARGIN, LEFT_W, PANEL_H

    c.saveState()
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.8)
    c.rect(lx, ly, lw, lh, fill=1, stroke=1)

    if pdf_path and os.path.exists(pdf_path):
        try:
            doc  = fitz.open(pdf_path)
            page = doc[0]
            mat  = fitz.Matrix(3.0, 3.0)
            pix  = page.get_pixmap(matrix=mat, alpha=False)
            doc.close()

            img     = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            tmp_png = os.path.join(tmp_dir, f'prev_{os.path.basename(pdf_path)}.png')
            img.save(tmp_png, 'PNG')

            pad    = 4 * mm
            max_w  = lw - 2 * pad
            max_h  = lh - 2 * pad
            iw, ih = pix.width, pix.height
            scale  = min(max_w / (iw / 3.0), max_h / (ih / 3.0))
            dw     = (iw / 3.0) * scale
            dh     = (ih / 3.0) * scale
            dx     = lx + (lw - dw) / 2
            dy     = ly + (lh - dh) / 2
            c.drawImage(tmp_png, dx, dy, dw, dh)
        except Exception as e:
            c.setFont(font, 9)
            c.setFillColor(C_BORDER)
            c.drawCentredString(lx + lw / 2, ly + lh / 2, f'PDF読み込みエラー: {e}')

    # PDF未指定 or 未検出 → 空白（見本通り）
    c.restoreStore() if hasattr(c, 'restoreStore') else c.restoreState()


# ════════════════════════════════════════════════════
#  右パネル: シンプル罫線フォーム
# ════════════════════════════════════════════════════
def build_right(df, row, page_no, total, font, avail_w):
    W     = avail_w
    story = []

    # ── タイトル行 ─────────────────────────────────
    title_t = Table(
        [[P(CATALOG_TITLE, font, 11, C_BLACK, 'left'),
          P(f'P.{page_no:02d}', font, 11, C_BLACK, 'right')]],
        colWidths=[W * 0.75, W * 0.25]
    )
    title_t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(title_t)

    # 横罫線
    rule = Table([['']], colWidths=[W])
    rule.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.8, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(rule)
    story.append(Spacer(1, 4 * mm))

    # ── 上段：基本情報テーブル ──────────────────────
    LW1 = 18 * mm
    VW1 = W / 2 - LW1

    def lbl1(t): return P(t, font, 8.5, C_DGRAY, 'center')
    def val1(t): return P(t, font, 10,  C_BLACK, 'left')

    date_fmt  = format_date(get(row, 'date'))       # ② ○月○日に変換
    studio_v  = get(row, 'studio')
    time_v    = get(row, 'time')
    client_v  = get(row, 'client')
    product_v = get(row, 'product_name')
    sub_page  = f"{get(row,'subject')} / {get(row,'pub_page')}p"

    info_t = Table(
        [[lbl1('撮影日'),   val1(date_fmt),   lbl1('スタジオ'),    val1(studio_v)],
         [lbl1('撮影時間'), val1(time_v),     lbl1('担当'),        val1(client_v)],
         [lbl1('商品名'),   val1(product_v),  lbl1('教科／掲載頁'), val1(sub_page)]],
        colWidths=[LW1, VW1, LW1, VW1]
    )
    info_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (0,-1), C_LABEL),
        ('BACKGROUND',    (2,0), (2,-1), C_LABEL),
        ('GRID',          (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
        ('ALIGN',         (2,0), (2,-1), 'CENTER'),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 5 * mm))

    # ── 下段：撮影詳細テーブル ─────────────────────
    LW2 = 22 * mm
    VW2 = W - LW2
    ROW_H = 9 * mm

    def lbl2(t): return P(t, font, 8.5, C_DGRAY, 'center')
    def val2(t, size=10): return P(t, font, size, C_BLACK, 'left')

    # ③ 撮影ナンバー: J×K が同じ全行の M列を「／」で連結
    shoot_no = get_shoot_numbers(df, row)

    # ④ 各欄の参照列
    cnt_single  = get(row, 'cnt_single')   # O列
    cnt_model   = get(row, 'cnt_model')    # P列
    mdl_name_v  = get(row, 'mdl_name')    # V列のみ（単独）
    cnt_image   = get(row, 'cnt_image')   # Q列
    cnt_feature = get(row, 'cnt_feature') # R列
    background  = get(row, 'background')
    equipment   = get(row, 'equipment')
    remarks_v   = get(row, 'remarks')

    det_t = Table(
        [[lbl2('撮影ナンバー'),     val2(shoot_no, 11)],
         [lbl2('単品撮影'),         val2(cnt_single)],
         [lbl2('モデル撮影'),       val2(cnt_model)],
         [lbl2('モデル名'),         val2(mdl_name_v)],
         [lbl2('イメージ撮影'),     val2(cnt_image)],
         [lbl2('特徴'),             val2(cnt_feature)],
         [lbl2('建て込み／\n白背景'), val2(background)],
         [lbl2('必要な備品'),       val2(equipment)],
         [lbl2('備考'),             val2(remarks_v)]],
        colWidths=[LW2, VW2],
        rowHeights=[ROW_H] * 9
    )
    det_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (0,-1), C_LABEL),
        ('GRID',          (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
    ]))
    story.append(det_t)
    return story


# ════════════════════════════════════════════════════
#  PDF出力メイン
# ════════════════════════════════════════════════════
def build_pdf(df, output_path, font, pdf_dir=None):
    """
    df        : load_excel() で読み込んだ DataFrame
    output_path: 出力先パス
    font      : setup_font() で返されたフォント名
    pdf_dir   : PDFファイルを探す追加ディレクトリ（Streamlit用）
    """
    total = len(df)

    def resolve_pdf(path):
        """パスが存在しない場合、pdf_dir からファイル名で検索"""
        if path and os.path.exists(path):
            return path
        if pdf_dir and path:
            basename = os.path.basename(path)
            candidate = os.path.join(pdf_dir, basename)
            if os.path.exists(candidate):
                return candidate
        return path  # 見つからなくてもパスをそのまま返す（空白表示）

    with tempfile.TemporaryDirectory() as tmp_dir:
        c = pdf_canvas.Canvas(output_path, pagesize=landscape(A3))

        for pg_idx, (_, row) in enumerate(df.iterrows()):
            if pg_idx > 0:
                c.showPage()

            pdf_path = resolve_pdf(get(row, 'pdf_path'))

            render_left(c, pdf_path, tmp_dir, font)

            right_story = build_right(df, row, pg_idx + 1, total, font, RIGHT_W)
            f = Frame(RIGHT_X, MARGIN, RIGHT_W, PANEL_H, id='right',
                      leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0,
                      showBoundary=0)
            f.addFromList(right_story, c)

        c.save()

    print(f'✅ PDF生成完了: {output_path}  ({total}ページ)')
    for i, (_, row) in enumerate(df.iterrows()):
        print(f'   p.{i+1:02d}: {get(row,"filename")}  {get(row,"product_name")}')


# ════════════════════════════════════════════════════
#  エントリポイント（スタンドアロン実行用）
# ════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print('使用方法: python convert_shooting_sheet.py 入力.xlsx [出力.pdf]')
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(inp)[0] + '_撮影シート.pdf'
    if not os.path.exists(inp):
        print(f'❌ ファイルが見つかりません: {inp}')
        sys.exit(1)
    print(f'📂 {inp}')
    font = setup_font()
    df   = load_excel(inp)
    build_pdf(df, out, font)


if __name__ == '__main__':
    main()
