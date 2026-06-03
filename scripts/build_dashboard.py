# -*- coding: utf-8 -*-
"""
Atualiza o bloco DATA dentro de Dashboard_Estoque_GYP.html
com os dados mais recentes processados pelo processar_estoque.py.

Lê os CSVs de %TEMP%/gyp_estoque e gera o JSON DATA, substituindo
no HTML existente. Não altera CSS/JS — apenas os dados.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import os, json, re, tempfile
from datetime import datetime
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
HTML_PATH  = os.path.join(ROOT, 'Dashboard_Estoque_GYP.html')
TMP        = os.environ.get('GYP_TMP', os.path.join(tempfile.gettempdir(),'gyp_estoque'))

if not os.path.exists(HTML_PATH):
    print(f"AVISO: {HTML_PATH} não existe - dashboard sera pulado.")
    raise SystemExit(0)

print("Carregando CSVs intermediários...")
estoque = pd.read_csv(os.path.join(TMP,'estoque_completo.csv'))
estoque['Data de Vencimento'] = pd.to_datetime(estoque['Data de Vencimento'], errors='coerce')

TODAY = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)

# ── Limpar nome de família (remover prefixo "1 - ") ─────────────
def fam_clean(f):
    s = str(f)
    if ' - ' in s:
        return s.split(' - ',1)[1]
    return s
estoque['Familia_Clean'] = estoque['Familia'].apply(fam_clean)

# ── KPIs ─────────────────────────────────────────────────────────
crit  = int(((estoque['Dias p/ Vencer']>=0) & (estoque['Dias p/ Vencer']<=60)).sum())
aten  = int(((estoque['Dias p/ Vencer']>60) & (estoque['Dias p/ Vencer']<=120)).sum())
ok    = int(((estoque['Dias p/ Vencer']>120) & (estoque['Dias p/ Vencer']<=183)).sum())
venc  = int((estoque['Dias p/ Vencer']<0).sum())

kpis = {
    'total_registros': int(len(estoque)),
    'total_skus': int(estoque['Código do Produto'].nunique()),
    'total_estoque': int(estoque['Estoque (UN)'].sum()),
    'vencidos_fora_count': venc,
    'critico_count': crit,
    'atencao_count': aten,
    'ok_count': ok,
    'data_ref': TODAY.strftime('%d/%m/%Y'),
}

# ── Família totais ──────────────────────────────────────────────
fam_grp = estoque.groupby('Familia_Clean')['Estoque (UN)'].sum().reset_index()
fam_grp = fam_grp.rename(columns={'Familia_Clean':'familia','Estoque (UN)':'estoque'})
fam_grp = fam_grp.sort_values('estoque', ascending=False)
familia = fam_grp.to_dict('records')

# ── Próximos de Vencer (<=183d, >=0d) ───────────────────────────
prox = estoque[(estoque['Dias p/ Vencer']>=0) & (estoque['Dias p/ Vencer']<=183)].copy()

def urg(d):
    if d<=60:  return 'Crítico'
    if d<=120: return 'Atenção'
    return 'OK'
prox['urgencia'] = prox['Dias p/ Vencer'].apply(urg)

prox_tab = [{
    'local': str(r.get('Local','')),
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'familia': fam_clean(r['Familia']),
    'lote': str(r.get('Lote','')),
    'lote_ind': str(r.get('Lote Indústria','')),
    'estoque': float(r['Estoque (UN)']),
    'vencimento': r['Data de Vencimento'].strftime('%d/%m/%Y') if pd.notna(r['Data de Vencimento']) else '',
    'dias': int(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) else None,
    'urgencia': r['urgencia'],
} for _, r in prox.iterrows()]

# Para chart de família × urgência
prox_chart_rows = prox.groupby(['Familia_Clean','urgencia'])['Estoque (UN)'].sum().reset_index()
prox_chart = [{
    'familia': r['Familia_Clean'],
    'urgencia': r['urgencia'],
    'estoque': float(r['Estoque (UN)'])
} for _, r in prox_chart_rows.iterrows()]

# ── Vencidos fora do setor ───────────────────────────────────────
SETOR_VEN = '[1102] GYP - VENCIDOS (G9)'
venc_df = estoque[(estoque['Dias p/ Vencer']<0) & (estoque.get('Setor','')!=SETOR_VEN)].copy()
venc_fora = [{
    'local': str(r.get('Local','')),
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'familia': fam_clean(r['Familia']),
    'linha': str(r.get('Linha','')),
    'setor': str(r.get('Setor','')),
    'lote': str(r.get('Lote','')),
    'estoque': float(r['Estoque (UN)']),
    'vencimento': r['Data de Vencimento'].strftime('%d/%m/%Y') if pd.notna(r['Data de Vencimento']) else '',
    'dias': int(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) else None,
} for _, r in venc_df.iterrows()]

# Vencidos por família (chart + resumo)
venc_por_familia_df = venc_df.groupby('Familia_Clean')['Estoque (UN)'].sum().reset_index()
venc_por_familia_df = venc_por_familia_df.sort_values('Estoque (UN)', ascending=False)
venc_por_familia = [{'familia':r['Familia_Clean'],'estoque':float(r['Estoque (UN)'])} for _,r in venc_por_familia_df.iterrows()]

# ── Produto Acabado (compilado por linha) ───────────────────────
pa_df = estoque[estoque['Familia']=='4 - Produto Acabado'].copy()
pa_grp = pa_df.groupby(['Código do Produto','Produto','Linha']).agg(
    estoque=('Estoque (UN)','sum'),
    menor_venc=('Data de Vencimento','min')
).reset_index()
pa_grp['menor_venc_str'] = pa_grp['menor_venc'].apply(lambda v: v.strftime('%d/%m/%Y') if pd.notna(v) else '-')
pa_list = [{
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'linha': str(r['Linha']) if str(r['Linha']) else 'OUTROS',
    'estoque': float(r['estoque']),
    'menor_venc': r['menor_venc_str'],
} for _, r in pa_grp.iterrows()]

# Linha totais
lt_df = pa_grp.groupby('Linha')['estoque'].sum().reset_index()
lt_df = lt_df.sort_values('estoque', ascending=False)
linha_totais = [{'linha': str(r['Linha']) if str(r['Linha']) else 'OUTROS', 'total': float(r['estoque'])} for _, r in lt_df.iterrows()]

# ── Saldo Completo (para botão Exportar Saldo Completo) ─────────
saldo_completo = [{
    'local': str(r.get('Local','')),
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'familia': fam_clean(r['Familia']),
    'linha': str(r.get('Linha','')),
    'setor': str(r.get('Setor','')),
    'lote': str(r.get('Lote','')),
    'lote_ind': str(r.get('Lote Indústria','')),
    'estoque': float(r['Estoque (UN)']),
    'vencimento': r['Data de Vencimento'].strftime('%d/%m/%Y') if pd.notna(r['Data de Vencimento']) else '',
    'dias': int(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) else None,
    'urgencia': (urg(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) and r['Dias p/ Vencer']>=0
                 else ('Vencido' if pd.notna(r['Dias p/ Vencer']) else 'Longa Validade')),
} for _, r in estoque.iterrows()]

# ── Monta DATA final ────────────────────────────────────────────
DATA = {
    'kpis': kpis,
    'familia': familia,
    'prox_tab': prox_tab,
    'prox_chart': prox_chart,
    'venc_fora': venc_fora,
    'venc_por_familia': venc_por_familia,
    'pa_list': pa_list,
    'linha_totais': linha_totais,
    'saldo_completo': saldo_completo,
}

data_str = json.dumps(DATA, ensure_ascii=False, separators=(',',':'))
print(f"DATA gerado: {len(data_str):,} chars")

# ── Substituir bloco DATA no HTML ───────────────────────────────
print("Atualizando HTML...")
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

new_html, n = re.subn(
    r'const DATA\s*=\s*\{.*?\};',
    f'const DATA = {data_str};',
    html, count=1, flags=re.DOTALL
)
if n == 0:
    print("ERRO: bloco DATA não encontrado no HTML.")
    raise SystemExit(1)

# Atualizar referência de data nos badges
new_html = re.sub(
    r'Ref\.\s*\d{2}/\d{2}/\d{4}',
    f"Ref. {kpis['data_ref']}",
    new_html
)

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"[OK] Dashboard atualizado: {HTML_PATH}")
print(f"  Famílias: {len(familia)} | Próximos: {len(prox_tab)} | Vencidos: {len(venc_fora)} | PA: {len(pa_list)} | Saldo total: {len(saldo_completo)}")
