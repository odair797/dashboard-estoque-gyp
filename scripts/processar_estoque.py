# -*- coding: utf-8 -*-
"""
Processa o TSV exportado do Senior e gera:
  - CSVs intermediarios em %TEMP%/gyp_estoque/
  - output/Analise_Estoque_GYP.xlsx
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import sys, os, glob, subprocess, tempfile
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
INPUT_DIR  = os.path.join(ROOT, 'input')
OUTPUT_DIR = os.path.join(ROOT, 'output')
TMP_DIR    = os.path.join(tempfile.gettempdir(), 'gyp_estoque')
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

if len(sys.argv) > 1:
    TSV_PATH = sys.argv[1]
else:
    tsvs = glob.glob(os.path.join(INPUT_DIR, '*.tsv')) + glob.glob(os.path.join(INPUT_DIR, '*.txt'))
    if not tsvs:
        print("ERRO: nenhum .tsv encontrado em input/"); sys.exit(1)
    TSV_PATH = max(tsvs, key=os.path.getmtime)
print(f"[1/3] Arquivo de entrada: {os.path.basename(TSV_PATH)}")

TODAY     = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
OUT_EXCEL = os.path.join(OUTPUT_DIR, 'Analise_Estoque_GYP.xlsx')
print(f"[1/3] Data base: {TODAY.strftime('%d/%m/%Y')}")

print("[2/3] Lendo dados...")
df = pd.read_csv(TSV_PATH, sep='\t', low_memory=False, encoding='utf-8-sig')
df['Data de Vencimento'] = pd.to_datetime(df['Data de Vencimento'], errors='coerce', dayfirst=True)
df['Estoque (UN)']       = pd.to_numeric(df.get('Estoque (UN)', df.get('Estoque', 0)), errors='coerce').fillna(0)

def get_familia(code):
    c = str(code).strip()
    m = {'1':'1 - Materia Prima','2':'2 - Embalagem','3':'3 - Granel',
         '4':'4 - Produto Acabado','5':'5 - Apoio'}
    return m.get(c[0], 'Outros') if c else 'Outros'

df['Familia'] = df['Codigo do Produto'].apply(get_familia) if 'Codigo do Produto' in df.columns else df['Código do Produto'].apply(get_familia)
df['Dias p/ Vencer']  = (df['Data de Vencimento'] - TODAY).dt.days
df['Meses p/ Vencer'] = (df['Dias p/ Vencer'] / 30.0).round(1)

def criticidade(d):
    if pd.isna(d):  return 'SEM DATA'
    if d < 0:       return 'VENCIDO'
    if d <= 60:     return 'CRITICO <=60d'
    if d <= 120:    return 'ATENCAO <=120d'
    if d <= 180:    return 'PROXIMO <=180d'
    return 'OK'

df['Criticidade'] = df['Dias p/ Vencer'].apply(criticidade)

def classificar_linha(nome):
    # A linha comercial e o prefixo do nome do produto antes de " - ".
    # Ex.: "TERRA COCO - SHAMPOO 1L" -> "TERRA COCO".
    # Produtos sem " - " que sejam kits viram "KITS"; senao usam o nome todo.
    # Assim todo SKU recebe a sua linha real e nada fica em "OUTROS".
    n = str(nome).strip()
    if ' - ' in n:
        return n.split(' - ', 1)[0].upper().strip()
    u = n.upper()
    if 'KIT' in u:
        return 'KITS'
    return u

df['Linha'] = df.apply(lambda r: classificar_linha(r['Produto']) if r['Familia']=='4 - Produto Acabado' else '', axis=1)

estoque = df[df['Estoque (UN)'] > 0].copy()
if 'Setor' not in estoque.columns:
    estoque['Setor'] = ''

print("[2/3] Salvando intermediarios...")
sku_col = 'Codigo do Produto' if 'Codigo do Produto' in estoque.columns else 'Código do Produto'
cols_padrao_pa = ['Linha',sku_col,'Produto','Estoque (UN)','Lote','Local','Setor',
                  'Data de Vencimento','Dias p/ Vencer','Meses p/ Vencer','Criticidade']
cols_padrao    = [sku_col,'Produto','Estoque (UN)','Lote','Local','Setor',
                  'Data de Vencimento','Dias p/ Vencer','Meses p/ Vencer','Criticidade']

pa = estoque[estoque['Familia']=='4 - Produto Acabado'][cols_padrao_pa].copy()
pa = pa.sort_values(['Linha','Produto','Dias p/ Vencer'], na_position='last')
pa.to_csv(os.path.join(TMP_DIR, 'fam_PA.csv'), index=False)

for fam_label, fam_short in [('1 - Materia Prima','MP'),('2 - Embalagem','EMB'),
                              ('3 - Granel','GRA'),('5 - Apoio','APO')]:
    sub = estoque[estoque['Familia']==fam_label][cols_padrao].copy()
    sub = sub.sort_values(['Dias p/ Vencer','Produto'], na_position='last')
    sub.to_csv(os.path.join(TMP_DIR, f'fam_{fam_short}.csv'), index=False)
    print(f"   {fam_label}: {len(sub):,} registros")

print(f"   4 - Produto Acabado: {len(pa):,} registros | Linhas: {pa['Linha'].nunique()}")

estoque.to_csv(os.path.join(TMP_DIR, 'estoque_completo.csv'), index=False)

print("[3/3] Gerando Excel...")
build_excel = os.path.join(SCRIPT_DIR, 'build_excel_v9.py')
env = os.environ.copy()
env['GYP_TMP'] = TMP_DIR
env['GYP_OUT'] = OUTPUT_DIR
env['PYTHONIOENCODING'] = 'utf-8'
r = subprocess.run([sys.executable, build_excel], capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=120)
if r.returncode != 0:
    print("   ERRO:\n" + (r.stderr or "")[:800]); sys.exit(1)
print((r.stdout or "").strip())

print()
print(f"OK EXTRACAO CONCLUIDA - {TODAY.strftime('%d/%m/%Y')}")
print(f"   Excel: {OUT_EXCEL}")
