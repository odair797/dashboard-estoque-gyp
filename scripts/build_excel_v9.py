# -*- coding: utf-8 -*-
"""
Gera Analise_Estoque_GYP.xlsx — modelo padrão:
  - Produto Acabado : Linha + 9 colunas padrão
  - Matéria Prima / Embalagem / Granel / Apoio : 9 colunas padrão
Colunas padrão: SKU, Descrição, Quantidade, Lote, Local,
                Data de Vencimento, Dias a Vencer, Meses a Vencer, Criticidade.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import os
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

WORKSPACE = os.environ.get('GYP_OUT', '.')
OUT_XLSX  = os.path.join(WORKSPACE, 'Analise_Estoque_GYP.xlsx')
TODAY     = datetime.today()
DATA_STR  = TODAY.strftime('%d/%m/%Y')

# Paleta
DARK_BG='1B2330'; GOLD='C9A961'; WHITE='FFFFFF'
RED_CRIT='C0392B'; ORG_ATEN='D68910'; YEL_PROX='F1C40F'
GREEN_OK='27AE60'; GRAY_BAND='EAECEE'; LINHA_BG='34495E'; NO_DATA='7F8C8D'

thin = Border(left=Side(style='thin', color='B0B0B0'),
              right=Side(style='thin', color='B0B0B0'),
              top=Side(style='thin', color='B0B0B0'),
              bottom=Side(style='thin', color='B0B0B0'))

def title_row(ws, row, ncols, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name='Calibri', size=14, bold=True, color=GOLD)
    c.fill = PatternFill('solid', fgColor=DARK_BG)
    c.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[row].height = 28

def header_row(ws, row, headers):
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = Font(name='Calibri', size=10, bold=True, color=WHITE)
        c.fill = PatternFill('solid', fgColor=DARK_BG)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = thin
    ws.row_dimensions[row].height = 36

CRIT_FILL = {
    'VENCIDO':       (RED_CRIT, WHITE),
    'CRÍTICO ≤60d':  (RED_CRIT, WHITE),
    'ATENÇÃO ≤120d': (ORG_ATEN, WHITE),
    'PRÓXIMO ≤180d': (YEL_PROX, '000000'),
    'OK':            (GREEN_OK, WHITE),
    'SEM DATA':      (NO_DATA, WHITE),
}

def fmt_data(v):
    if pd.isna(v) or v == '': return ''
    try: return pd.to_datetime(v).strftime('%d/%m/%Y')
    except: return v

def write_row(ws, row, valores, has_linha=False):
    band = GRAY_BAND if (row % 2 == 0) else WHITE
    for i, v in enumerate(valores, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name='Calibri', size=9)
        c.border = thin
        c.fill = PatternFill('solid', fgColor=band)
        c.alignment = Alignment(horizontal='center', vertical='center')
        # Coluna Descrição = alinhar à esquerda
        if (has_linha and i == 3) or (not has_linha and i == 2):
            c.alignment = Alignment(horizontal='left', vertical='center')
        # Coluna Local (5 ou 6) também à esquerda? — só centralizado fica ok
    # Formatar números
    off = 1 if has_linha else 0
    # Quantidade
    qcol = 4 + off
    ws.cell(row=row, column=qcol).number_format = '#,##0.000'
    # Dias a Vencer
    ws.cell(row=row, column=7+off).number_format = '0'
    # Meses a Vencer
    ws.cell(row=row, column=8+off).number_format = '0.0'
    # Criticidade (última coluna)
    crit_col = 9 + off
    crit_val = valores[crit_col-1]
    if crit_val in CRIT_FILL:
        bg, fg = CRIT_FILL[crit_val]
        c = ws.cell(row=row, column=crit_col)
        c.fill = PatternFill('solid', fgColor=bg)
        c.font = Font(name='Calibri', size=9, bold=True, color=fg)

# ── HEADERS PADRÃO ────────────────────────────────────────────────
HDRS_FAM = ['SKU','Descrição','Quantidade','Lote Indústria','Local',
            'Data de Vencimento','Dias a Vencer','Meses a Vencer','Criticidade']
HDRS_PA  = ['Linha'] + HDRS_FAM
WID_FAM  = [16, 42, 13, 18, 12, 14, 12, 12, 16]
WID_PA   = [18] + WID_FAM

wb = Workbook()
wb.remove(wb.active)

# ═══ ABA PRODUTO ACABADO ════════════════════════════════════════
TMP = os.environ.get('GYP_TMP','/tmp')
pa = pd.read_csv(os.path.join(TMP,'fam_PA.csv'))
ws = wb.create_sheet('📦 Produto Acabado')
title_row(ws, 1, len(HDRS_PA), f'PRODUTO ACABADO  |  {len(pa)} registros  |  {DATA_STR}')
header_row(ws, 2, HDRS_PA)

row = 3
for linha, grupo in pa.groupby('Linha', sort=True):
    # Sub-cabeçalho da linha
    n_reg = len(grupo)
    qtd_total = grupo['Estoque (UN)'].sum()
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(HDRS_PA))
    txt = f'  ▶  {linha or "(sem linha)"}   —   {n_reg} registros   |   Quantidade total: {qtd_total:,.0f}'.replace(',','.')
    c = ws.cell(row=row, column=1, value=txt)
    c.font = Font(name='Calibri', size=11, bold=True, color=GOLD)
    c.fill = PatternFill('solid', fgColor=LINHA_BG)
    c.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[row].height = 22
    row += 1

    for _, r in grupo.iterrows():
        valores = [
            '',  # Linha (em branco no detalhe)
            r.get('Código do Produto',''),
            r.get('Produto',''),
            float(r.get('Estoque (UN)',0) or 0),
            r.get('Lote Indústria',''),
            r.get('Local',''),
            fmt_data(r.get('Data de Vencimento','')),
            (int(r['Dias p/ Vencer']) if pd.notna(r.get('Dias p/ Vencer')) else ''),
            (float(r['Meses p/ Vencer']) if pd.notna(r.get('Meses p/ Vencer')) else ''),
            r.get('Criticidade',''),
        ]
        write_row(ws, row, valores, has_linha=True)
        row += 1

for i,w in enumerate(WID_PA,1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = 'A3'

# ═══ ABAS POR FAMÍLIA ═══════════════════════════════════════════
familias = [
    ('MP',  '🧪 Matéria Prima', 'MATÉRIA PRIMA'),
    ('EMB', '📦 Embalagem',     'EMBALAGEM'),
    ('GRA', '🛢️ Granel',         'GRANEL'),
    ('APO', '🔧 Apoio',         'APOIO'),
]

for short, sheet_name, fam_upper in familias:
    sub = pd.read_csv(os.path.join(TMP, f'fam_{short}.csv'))
    wsf = wb.create_sheet(sheet_name)
    title_row(wsf, 1, len(HDRS_FAM), f'{fam_upper}  |  {len(sub)} registros  |  {DATA_STR}')
    header_row(wsf, 2, HDRS_FAM)
    row = 3
    for _, r in sub.iterrows():
        valores = [
            r.get('Código do Produto',''),
            r.get('Produto',''),
            float(r.get('Estoque (UN)',0) or 0),
            r.get('Lote Indústria',''),
            r.get('Local',''),
            fmt_data(r.get('Data de Vencimento','')),
            (int(r['Dias p/ Vencer']) if pd.notna(r.get('Dias p/ Vencer')) else ''),
            (float(r['Meses p/ Vencer']) if pd.notna(r.get('Meses p/ Vencer')) else ''),
            r.get('Criticidade',''),
        ]
        write_row(wsf, row, valores, has_linha=False)
        row += 1
    for i,w in enumerate(WID_FAM,1):
        wsf.column_dimensions[get_column_letter(i)].width = w
    wsf.freeze_panes = 'A3'

wb.save(OUT_XLSX)
print(f'[OK] Excel: {OUT_XLSX}')
print(f'  Abas ({len(wb.sheetnames)}): {wb.sheetnames}')
