# -*- coding: utf-8 -*-
"""
Atualiza o bloco DATA dentro de Dashboard_Estoque_GYP.html
com os dados mais recentes processados pelo processar_estoque.py.
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
    print("AVISO: HTML nao existe - dashboard sera pulado.")
    raise SystemExit(0)

print("Carregando CSVs intermediarios...")
estoque = pd.read_csv(os.path.join(TMP,'estoque_completo.csv'))
estoque['Data de Vencimento'] = pd.to_datetime(estoque['Data de Vencimento'], errors='coerce')

TODAY = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)

# Limpar nome de familia (remover prefixo "1 - "); MP com acento p/ casar com o front-end
def fam_clean(f):
    s = str(f)
    if ' - ' in s:
        s = s.split(' - ', 1)[1]
    if s.strip().lower() == 'materia prima':
        return 'Matéria Prima'
    return s
estoque['Familia_Clean'] = estoque['Familia'].apply(fam_clean)

# KPIs
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
    'data_ref': datetime.now().strftime('%d/%m/%Y %H:%M'),
}

# Familia totais (Materia Prima ja vem em kg via Estoque (UN))
fam_grp = estoque.groupby('Familia_Clean')['Estoque (UN)'].sum().reset_index()
fam_grp = fam_grp.rename(columns={'Familia_Clean':'familia','Estoque (UN)':'estoque'})
fam_grp = fam_grp.sort_values('estoque', ascending=False)
familia = fam_grp.to_dict('records')

# Distribuicao do saldo por status operacional (por familia) -> subpaineis do Resumo
def _ssum(sub, pat):
    return float(sub[sub['Setor'].astype(str).str.contains(pat, case=False, na=False)]['Estoque (UN)'].sum())
for _rec in familia:
    _sub = estoque[estoque['Familia_Clean']==_rec['familia']]
    _rec['dist'] = {
        'avaria':    _ssum(_sub, 'AVARIA|BLOQUEAD'),
        'vencido':   _ssum(_sub, 'VENCIDO'),
        'reprovado': _ssum(_sub, 'REPROVAD'),
        'perdas':    _ssum(_sub, 'PERDAS'),
        'doca':      _ssum(_sub, 'DOCA'),
        'packing':   _ssum(_sub, 'PACKING'),
    }
    _rec['dist']['disponivel'] = float(_rec['estoque']) - sum(_rec['dist'].values())

# Detalhamento dos indicadores operacionais por familia (subpaineis do Resumo)
_fam_order = [r['familia'] for r in familia]
_dias = estoque['Dias p/ Vencer']
_masks = {
    'critico': (_dias>=0) & (_dias<=60),
    'atencao': (_dias>60) & (_dias<=120),
    'ok':      (_dias>120) & (_dias<=183),
    'vencidos':(_dias<0),
}
_sku_by_fam = estoque.groupby('Familia_Clean')['Código do Produto'].nunique().to_dict()
fam_breakdown = {'skus': {f:int(_sku_by_fam.get(f,0)) for f in _fam_order}}
for _key,_mask in _masks.items():
    _c = estoque[_mask].groupby('Familia_Clean').size().to_dict()
    fam_breakdown[_key] = {f:int(_c.get(f,0)) for f in _fam_order}
kpis['fam_breakdown'] = fam_breakdown

def unidade_fam(fam):
    return 'kg' if str(fam) == 'Matéria Prima' else 'un'

# Proximos de Vencer (<=183d, >=0d)
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
    'unidade': unidade_fam(fam_clean(r['Familia'])),
    'lote': str(r.get('Lote','')),
    'lote_ind': str(r.get('Lote Indústria','')),
    'estoque': float(r['Estoque (UN)']),
    'vencimento': r['Data de Vencimento'].strftime('%d/%m/%Y') if pd.notna(r['Data de Vencimento']) else '',
    'dias': int(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) else None,
    'urgencia': r['urgencia'],
} for _, r in prox.iterrows()]

prox_chart_rows = prox.groupby(['Familia_Clean','urgencia'])['Estoque (UN)'].sum().reset_index()
prox_chart = [{
    'familia': r['Familia_Clean'],
    'urgencia': r['urgencia'],
    'estoque': float(r['Estoque (UN)'])
} for _, r in prox_chart_rows.iterrows()]

# Vencidos fora do setor
SETOR_VEN = '[1102] GYP - VENCIDOS (G9)'
venc_df = estoque[(estoque['Dias p/ Vencer']<0) & (estoque.get('Setor','')!=SETOR_VEN)].copy()
venc_fora = [{
    'local': str(r.get('Local','')),
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'familia': fam_clean(r['Familia']),
    'unidade': unidade_fam(fam_clean(r['Familia'])),
    'linha': str(r.get('Linha','')),
    'setor': str(r.get('Setor','')),
    'lote': str(r.get('Lote','')),
    'estoque': float(r['Estoque (UN)']),
    'vencimento': r['Data de Vencimento'].strftime('%d/%m/%Y') if pd.notna(r['Data de Vencimento']) else '',
    'dias': int(r['Dias p/ Vencer']) if pd.notna(r['Dias p/ Vencer']) else None,
} for _, r in venc_df.iterrows()]

venc_por_familia_df = venc_df.groupby('Familia_Clean')['Estoque (UN)'].sum().reset_index()
venc_por_familia_df = venc_por_familia_df.sort_values('Estoque (UN)', ascending=False)
venc_por_familia = [{'familia':r['Familia_Clean'],'estoque':float(r['Estoque (UN)'])} for _,r in venc_por_familia_df.iterrows()]

# Produto Acabado (compilado por linha)
pa_df = estoque[estoque['Familia']=='4 - Produto Acabado'].copy()
# Considerar apenas estoque DISPONIVEL: excluir locais "em processo"
# Setores "em processo"/indisponiveis: DOCA, PACKING, AVARIA/BLOQUEADOS, REPROVADO, PERDAS.
# Esses PA nao contam no compilado nem no grafico por linha.
_setor_pa = pa_df.get('Setor', pd.Series('', index=pa_df.index)).astype(str)
_excluir = 'DOCA|PACKING|AVARIA|BLOQUEAD|REPROVAD|PERDAS'
pa_df = pa_df[~_setor_pa.str.contains(_excluir, case=False, na=False)].copy()
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

lt_df = pa_grp.groupby('Linha')['estoque'].sum().reset_index()
lt_df = lt_df.sort_values('estoque', ascending=False)
linha_totais = [{'linha': str(r['Linha']) if str(r['Linha']) else 'OUTROS', 'total': float(r['estoque'])} for _, r in lt_df.iterrows()]
GYP_LINHAS = [x['linha'] for x in linha_totais]

# Saldo Completo
saldo_completo = [{
    'local': str(r.get('Local','')),
    'sku': str(r['Código do Produto']),
    'produto': str(r['Produto']),
    'familia': fam_clean(r['Familia']),
    'unidade': unidade_fam(fam_clean(r['Familia'])),
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

# ====================== SALDO B2C (subpainel) ======================
# Le o saldo de estoque da B2C (export do Senior) de input/b2c/*.tsv|*.txt
# e gera KPIs + compilado por SKU. Arquivo separado para nao se misturar
# com o saldo principal (GYP/Senior).
import glob as _glob
B2C_DIR = os.path.join(ROOT, 'input', 'b2c')
def _build_b2c():
    files = _glob.glob(os.path.join(B2C_DIR, '*.tsv')) + _glob.glob(os.path.join(B2C_DIR, '*.txt'))
    if not files:
        return {'ok': False}
    path = max(files, key=os.path.getmtime)
    try:
        b = pd.read_csv(path, sep='\t', low_memory=False, encoding='utf-8-sig')
    except Exception as e:
        print('  [B2C] falha ao ler arquivo: ' + str(e))
        return {'ok': False}
    sku_c = 'Código do Produto' if 'Código do Produto' in b.columns else (
            'Codigo do Produto' if 'Codigo do Produto' in b.columns else None)
    if sku_c is None or 'Produto' not in b.columns:
        print('  [B2C] colunas obrigatorias ausentes (SKU/Produto).')
        return {'ok': False}
    b['__venc'] = pd.to_datetime(b.get('Data de Vencimento'), errors='coerce', dayfirst=True)
    b['__est']  = pd.to_numeric(b.get('Estoque (UN)', b.get('Estoque', 0)), errors='coerce').fillna(0)
    b = b[b['__est'] > 0].copy()
    if b.empty:
        return {'ok': False}
    b['__dias'] = (b['__venc'] - TODAY).dt.days
    b['__lote'] = b.get('Lote', '').astype(str)
    b['__local'] = b.get('Local', '').astype(str)

    def _crit(d):
        if pd.isna(d):   return 'Sem data'
        if d < 0:        return 'Vencido'
        if d <= 60:      return 'Crítico'
        if d <= 120:     return 'Atenção'
        return 'OK'

    grp = b.groupby([sku_c, 'Produto']).agg(
        estoque=('__est', 'sum'),
        lotes=('__lote', 'nunique'),
        locais=('__local', 'nunique'),
        menor_venc=('__venc', 'min'),
        menor_dias=('__dias', 'min'),
    ).reset_index().sort_values(sku_c, ascending=True, key=lambda c: c.astype(str))

    compilado = [{
        'sku': str(r[sku_c]),
        'produto': str(r['Produto']),
        'estoque': float(r['estoque']),
        'lotes': int(r['lotes']),
        'locais': int(r['locais']),
        'menor_venc': r['menor_venc'].strftime('%d/%m/%Y') if pd.notna(r['menor_venc']) else '-',
        'dias': int(r['menor_dias']) if pd.notna(r['menor_dias']) else None,
        'criticidade': _crit(r['menor_dias']),
    } for _, r in grp.iterrows()]

    _d = b['__dias']
    return {
        'ok': True,
        'arquivo': os.path.basename(path),
        'data_ref': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'kpis': {
            'registros': int(len(b)),
            'skus': int(b[sku_c].nunique()),
            'estoque': float(b['__est'].sum()),
            'proximos': int(((_d >= 0) & (_d <= 183)).sum()),
            'critico': int(((_d >= 0) & (_d <= 60)).sum()),
            'vencidos': int((_d < 0).sum()),
        },
        'compilado': compilado,
    }

b2c = _build_b2c()
if b2c.get('ok'):
    print('  [B2C] ' + str(b2c['kpis']['skus']) + ' SKUs | ' +
          format(int(b2c['kpis']['estoque']), ',') + ' un | arquivo: ' + b2c['arquivo'])
else:
    print('  [B2C] sem arquivo em input/b2c/ (subpainel ficara como aguardando).')


# ====================== SALDO LISA (modulo) ======================
# Le o saldo do sistema LISA (TXT largura fixa) de input/lisa/*.txt e
# converte o codigo Bling -> codigo Senior pela planilha de conversao
# (input/lisa/*.xlsx). Considera APENAS itens com SALDO DISPONIVEL > 0.
# SKUs sem conversao viram "pendencias" para descoberta do codigo Senior.
LISA_DIR = os.path.join(ROOT, 'input', 'lisa')

def _fam_nome(sku):
    return {'1':'Matéria Prima','2':'Embalagem','3':'Granel',
            '4':'Produto Acabado','5':'Apoio'}.get(str(sku)[:1], 'Outros')

def _lote_to_venc(lote, anos_vida=3, meses_critico=6):
    """Lote LISA: LL DD MM AA PPP -> (fabricacao, vencimento, dias, criticidade).
    Ex.: 01260428029 => seq=01 dia=26 mes=04 ano=28(2028) prod=029.
    Vencimento = fabricacao + anos_vida; critico = dentro de meses_critico do venc."""
    s = re.sub(r'\D', '', str(lote or ''))
    if len(s) < 8:
        return (None, None, None, None)
    try:
        dia = int(s[2:4]); mes = int(s[4:6]); ano = 2000 + int(s[6:8])
        fab = datetime(ano, mes, dia)
    except Exception:
        return (None, None, None, None)
    try:
        venc = fab.replace(year=fab.year + anos_vida)
    except ValueError:
        venc = fab.replace(year=fab.year + anos_vida, day=28)
    dias = (venc - TODAY).days
    if dias < 0:                     crit = 'Vencido'
    elif dias <= meses_critico * 30: crit = 'Crítico'
    else:                            crit = 'OK'
    return (fab, venc, dias, crit)

_MEDIDA_RE = re.compile(r"\s*\d+([.,]\d+)?\s*(ML|L|KG|GR|G|UN)\b\.?", re.IGNORECASE)

def _strip_medida(nome):
    """Remove a medida/volume do fim do nome (300ML, 250G, 1L...) e simbolos."""
    s = str(nome or "")
    s = _MEDIDA_RE.sub(" ", s)
    s = s.replace("\u00ae", "").replace("\u00a9", "")
    s = re.sub(r"\s*-\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -.")
    return s.upper().strip()

def _categoria_produto(nome):
    """Agrupa produtos sem linha pela categoria (1a palavra-tipo), igual pedido:
    'Leave-in 300ML' -> LEAVE-IN ; 'Mascara X 250G' -> MASCARAS. Usa startswith
    para so agrupar quando o tipo lidera o nome (marcas ja resolveram antes)."""
    n = str(nome or "").strip().lower()
    cats = [
        ("M\u00c1SCARAS",        ["m\u00e1scara", "mascara"]),
        ("LEAVE-IN",         ["leave-in", "leave in"]),
        ("SHAMPOOS",         ["shampoo"]),
        ("CONDICIONADORES",  ["condicionador"]),
        ("\u00d3LEOS",           ["\u00f3leo", "oleo"]),
        ("CREMES",           ["creme"]),
        ("S\u00c9RUNS",          ["s\u00e9rum", "serum"]),
        ("SPRAYS",           ["spray"]),
        ("T\u00d4NICOS",         ["t\u00f4nico", "tonico"]),
    ]
    for lab, kws in cats:
        if any(n.startswith(kw) for kw in kws):
            return lab
    return ""

def _linha_por_nome(nome, canon):
    """Deriva a Linha comercial pelo nome do produto (LISA nao traz linha).
    Usa a lista oficial de linhas do GYP (canon) + apelidos conhecidos."""
    n = str(nome or '').lower()
    cset = set(canon)
    alias = [
        ('ELIXIR DO PANTANAL', ['pantanal']),
        ('ELIXIR DO CERRADO',  ['cerrado']),
        ('ELIXIR DA FLORESTA', ['floresta', 'forest']),
        ('YBERA FASHION KIDS', ['fashion kids', 'kids menino', 'kids menina', 'kit kids']),
        ('POS-PROGRESSIVA',    ['pos-progressiva', 'p\u00f3s-progressiva', 'ph control']),
        ("LIFES FLOWER",       ["life's flower", 'lifes flower', "life`s flower"]),
    ]
    for ln, kws in alias:
        if ln in cset and any(kw in n for kw in kws):
            return ln
    if n.strip().startswith('kit') and 'KITS' in cset:
        return 'KITS'
    for c in sorted(cset, key=len, reverse=True):
        if c and c.lower() in n:
            return c
    # Fallback baseado nas linhas da GYP (classificar_linha em processar_estoque.py):
    # 1) prefixo antes de ' - '  2) KIT->KITS
    # 3) agrupa produtos sem prefixo por categoria (MASCARAS, SHAMPOOS, LEAVE-IN...)
    # 4) senao, nome sem a medida. Assim nada fica em OUTROS.
    raw = str(nome or '').strip()
    if ' - ' in raw:
        return raw.split(' - ', 1)[0].upper().strip()
    if 'KIT' in raw.upper():
        return 'KITS'
    cat = _categoria_produto(raw)
    if cat:
        return cat
    return _strip_medida(raw)

def _build_lisa():
    from collections import defaultdict
    txts = _glob.glob(os.path.join(LISA_DIR, '*.txt'))
    xlss = _glob.glob(os.path.join(LISA_DIR, '*.xlsx'))
    if not txts or not xlss:
        return {'ok': False}
    txt_path = max(txts, key=os.path.getmtime)
    xls_path = max(xlss, key=os.path.getmtime)

    # --- mapa de conversao Bling -> (Senior, Produto) ---
    try:
        rawc = pd.read_excel(xls_path, header=None)
    except Exception as e:
        print('  [LISA] falha ao ler conversao: ' + str(e)); return {'ok': False}
    hdr_idx = None
    for i in range(min(12, len(rawc))):
        vals = [str(v).strip().upper() for v in rawc.iloc[i].tolist()]
        if 'COD BLING' in vals:
            hdr_idx = i; break
    if hdr_idx is None:
        print('  [LISA] cabecalho COD BLING nao encontrado na conversao.'); return {'ok': False}
    hrow = [str(v).strip().upper() for v in rawc.iloc[hdr_idx].tolist()]
    ci_bling  = hrow.index('COD BLING')
    ci_senior = hrow.index('COD SÊNIOR') if 'COD SÊNIOR' in hrow else (hrow.index('COD SENIOR') if 'COD SENIOR' in hrow else None)
    ci_prod   = hrow.index('PRODUTO') if 'PRODUTO' in hrow else None
    def _norm(s): return re.sub(r'\s+', '', str(s)).upper()
    cmap = {}
    for _, r in rawc.iloc[hdr_idx+1:].iterrows():
        b = r.iloc[ci_bling]
        if pd.isna(b): continue
        bn = _norm(b)
        if not bn or bn == 'CODBLING': continue
        sen = r.iloc[ci_senior] if ci_senior is not None else None
        if pd.isna(sen): continue
        sen = str(sen).split('.')[0].strip()
        prod = str(r.iloc[ci_prod]).strip() if (ci_prod is not None and pd.notna(r.iloc[ci_prod])) else ''
        cmap[bn] = (sen, prod)

    # --- mapa Senior -> (linha, produto) a partir da base GYP ---
    sen_linha, sen_prod = {}, {}
    try:
        for _, br in estoque[['Código do Produto', 'Linha', 'Produto']].iterrows():
            k = str(br['Código do Produto']).split('.')[0]
            if k and k not in sen_linha:
                sen_linha[k] = str(br['Linha']) if pd.notna(br['Linha']) and str(br['Linha']).strip() else ''
                sen_prod[k]  = str(br['Produto'])
    except Exception:
        pass

    # --- parse LISA (largura fixa) ---
    raw = open(txt_path, encoding='latin-1', errors='replace').read().splitlines()
    if not raw: return {'ok': False}
    cut = lambda ln, a, b: ln[a:b].strip()
    items = []
    for ln in raw[1:]:
        if not ln.strip(): continue
        cod = cut(ln, 0, 31)
        if not cod: continue
        ds = cut(ln, 84, 111).replace('.', '').replace(',', '.')
        try: disp = float(ds)
        except: disp = 0.0
        if disp <= 0: continue   # APENAS disponivel
        items.append({'bling': cod, 'desc': cut(ln, 31, 84),
                      'disp': disp, 'armazem': cut(ln, 131, 149)})
    if not items:
        return {'ok': False}

    # --- conversao + agregacao por SKU Senior ---
    agg  = defaultdict(lambda: {'estoque': 0.0, 'blings': set(), 'armazens': set(), 'desc': ''})
    pend = defaultdict(lambda: {'estoque': 0.0, 'desc': '', 'armazens': set()})
    conv_blings = set()
    for it in items:
        bn = _norm(it['bling'])
        conv = cmap.get(bn)
        if conv:
            sen, prodc = conv
            conv_blings.add(bn)
            a = agg[sen]
            a['estoque'] += it['disp']
            a['blings'].add(it['bling'])
            if it['armazem']: a['armazens'].add(it['armazem'])
            if not a['desc']: a['desc'] = prodc or sen_prod.get(sen, '') or it['desc']
        else:
            p = pend[it['bling']]
            p['estoque'] += it['disp']
            if not p['desc']: p['desc'] = it['desc']
            if it['armazem']: p['armazens'].add(it['armazem'])

    compilado = []
    for sen, a in agg.items():
        _canon = GYP_LINHAS
        # Linha so para Produto Acabado (codigo inicia em 4), igual a GYP.
        if str(sen).startswith('4'):
            linha = sen_linha.get(sen, '') or _linha_por_nome(a['desc'] or sen_prod.get(sen, ''), _canon)
        else:
            linha = sen_linha.get(sen, '')
        compilado.append({
            'senior': sen,
            'produto': a['desc'] or sen_prod.get(sen, ''),
            'bling': ', '.join(sorted(a['blings'])),
            'familia': _fam_nome(sen),
            'linha': linha if linha else '—',
            'estoque': round(a['estoque'], 0),
            'armazens': ', '.join(sorted(a['armazens'])),
        })
    compilado.sort(key=lambda x: x['estoque'], reverse=True)

    pendencias = [{
        'bling': b, 'descricao': p['desc'], 'estoque': round(p['estoque'], 0),
        'armazem': ', '.join(sorted(p['armazens'])),
    } for b, p in pend.items()]
    pendencias.sort(key=lambda x: x['estoque'], reverse=True)

    fam_t = defaultdict(float); lin_t = defaultdict(float)
    for c in compilado:
        fam_t[c['familia']] += c['estoque']
        lin_t[c['linha'] if c['linha'] != '—' else 'OUTROS'] += c['estoque']
    familia      = sorted([{'familia': k, 'estoque': v} for k, v in fam_t.items()], key=lambda x: x['estoque'], reverse=True)
    linha_totais = sorted([{'linha': k, 'total': v} for k, v in lin_t.items()], key=lambda x: x['total'], reverse=True)

    # --- vencimento por lote (acende quando o export trouxer o campo Lote) ---
    tem_lote = any(it.get('lote') for it in items)
    prox, vencidos = [], []
    if tem_lote:
        for it in items:
            conv = cmap.get(_norm(it['bling']))
            if not conv: continue
            sen, prodc = conv
            fab, venc, dias, crit = _lote_to_venc(it.get('lote'))
            if venc is None: continue
            rec = {'senior': sen, 'produto': prodc or sen_prod.get(sen,'') or it['desc'],
                   'familia': _fam_nome(sen), 'linha': sen_linha.get(sen,'') or '—',
                   'lote': it.get('lote'), 'estoque': round(it['disp'],0),
                   'vencimento': venc.strftime('%d/%m/%Y'), 'dias': dias, 'criticidade': crit}
            if dias is not None and dias < 0: vencidos.append(rec)
            elif dias is not None and dias <= 183: prox.append(rec)
        prox.sort(key=lambda x: (x['dias'] if x['dias'] is not None else 99999))
        vencidos.sort(key=lambda x: (x['dias'] if x['dias'] is not None else 0))

    return {
        'ok': True,
        'arquivo': os.path.basename(txt_path),
        'conversao_arquivo': os.path.basename(xls_path),
        'data_ref': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'kpis': {
            'registros': len(items),
            'skus_bling': len({_norm(i['bling']) for i in items}),
            'skus_senior': len(agg),
            'estoque': round(sum(a['estoque'] for a in agg.values()), 0),
            'convertidos': len(conv_blings),
            'pendentes': len(pend),
            'estoque_pendente': round(sum(p['estoque'] for p in pend.values()), 0),
        },
        'familia': familia,
        'linha_totais': linha_totais,
        'compilado': compilado,
        'pendencias': pendencias,
        'prox': prox,
        'vencidos': vencidos,
        'tem_lote': tem_lote,
    }

lisa = _build_lisa()
if lisa.get('ok'):
    print('  [LISA] ' + str(lisa['kpis']['skus_senior']) + ' SKUs Senior | ' +
          str(lisa['kpis']['pendentes']) + ' pendencias | ' +
          format(int(lisa['kpis']['estoque']), ',') + ' un disp.')
else:
    print('  [LISA] sem arquivo em input/lisa/ (painel ficara como aguardando).')


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
    'b2c': b2c,
    'lisa': lisa,
}

data_str = json.dumps(DATA, ensure_ascii=False, separators=(',',':'))
print("DATA gerado: " + format(len(data_str), ',') + " chars")

print("Atualizando HTML...")
with open(HTML_PATH, 'rb') as f:
    _raw = f.read()
# Remove bytes nulos que corrompem o JavaScript no navegador
if b'\x00' in _raw:
    print("  Aviso: bytes nulos encontrados no template -- removendo...")
    _raw = _raw.replace(b'\x00', b'')
html = _raw.decode('utf-8', errors='replace')

# Seguranca: nao sobrescrever um HTML bom com uma leitura truncada
if '</html>' not in html or 'const DATA' not in html:
    print("ERRO: HTML existente parece truncado/invalido (sem </html> ou DATA).")
    print("      Abortando para nao danificar o dashboard.")
    raise SystemExit(1)

new_html, n = re.subn(
    r'const DATA\s*=\s*\{.*?\};',
    'const DATA = ' + data_str + ';',
    html, count=1, flags=re.DOTALL
)
if n == 0:
    print("ERRO: bloco DATA nao encontrado no HTML.")
    raise SystemExit(1)

_ref = kpis['data_ref']
# Badge "Ref." removido do layout -- linha abaixo mantida apenas para "Referencia: <span>" se existir
new_html = re.sub(r'(Referência: <span>)[^<]*(</span>)', r'\g<1>' + _ref + r'\g<2>', new_html, count=1)
def _milhar(n):
    return format(int(n), ',').replace(',', '.')
_cont = _milhar(kpis['total_registros']) + ' registros · ' + _milhar(kpis['total_skus']) + ' SKUs'
new_html = re.sub(r'[\d.,]+ registros · [\d.,]+ SKUs', _cont, new_html, count=1)

# Atualiza o selo "NN SKUs - NN linhas" da aba Compilado PA
_n_sku = len({x['sku'] for x in pa_list})
_n_lin = len({x['linha'] for x in pa_list})
new_html = re.sub(r'\d+\s*SKUs\s*·\s*\d+\s*linhas',
                  str(_n_sku) + ' SKUs · ' + str(_n_lin) + ' linhas',
                  new_html)

# Garantir que as funções de exportação Excel estão presentes
_EXPORT_JS = """
// ========== FUNCOES DE EXPORTACAO EXCEL ==========
function _xlsxDownload(rows, filename) {
  var ws = XLSX.utils.json_to_sheet(rows);
  var wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Dados');
  XLSX.writeFile(wb, filename);
}
function exportarExcel() {
  var rows = DATA.prox_tab.map(function(r) {
    return {'Local':r.local,'SKU':r.sku,'Produto':r.produto,'Família':r.familia,
            'Lote':r.lote,'Lote Indústria':r.lote_ind,'Estoque':r.estoque,
            'Vencimento':r.vencimento,'Dias p/ Vencer':r.dias,'Urgência':r.urgencia};
  });
  _xlsxDownload(rows, 'Proximos_Vencer.xlsx');
}
function exportarVencidos() {
  var rows = DATA.venc_fora.map(function(r) {
    return {'Local':r.local,'SKU':r.sku,'Produto':r.produto,'Família':r.familia,
            'Setor Atual':r.setor,'Lote':r.lote,'Estoque':r.estoque,
            'Vencimento':r.vencimento,'Dias Vencido':Math.abs(r.dias||0)};
  });
  _xlsxDownload(rows, 'Vencidos_Mover.xlsx');
}
function exportarSaldoCompleto() {
  var wb = XLSX.utils.book_new();
  var _proc=function(s){return /DOCA|PACKING/i.test(s||'');};
  var familias = [
    {key:'Produto Acabado', nome:'Produto Acabado', comLinha:true},
    {key:'Matéria Prima',   nome:'Matéria Prima',   comLinha:false},
    {key:'Embalagem',       nome:'Embalagem',        comLinha:false},
    {key:'Granel',          nome:'Granel',           comLinha:false},
    {key:'Apoio',           nome:'Apoio',            comLinha:false},
  ];
  familias.forEach(function(fam) {
    var dados = DATA.saldo_completo.filter(function(r){ return r.familia === fam.key && !_proc(r.setor); });
    var rows = dados.map(function(r) {
      var meses = (r.dias !== null && r.dias !== undefined) ? Math.round(r.dias/30*10)/10 : '';
      if (fam.comLinha) {
        return {'Linha':r.linha,'SKU':r.sku,'Descrição':r.produto,
                'Quantidade':r.estoque,'Lote Indústria':r.lote_ind,'Local':r.local,'Setor':r.setor,
                'Data de Vencimento':r.vencimento,'Dias a Vencer':r.dias,
                'Meses a Vencer':meses,'Criticidade':r.urgencia};
      } else {
        return {'SKU':r.sku,'Descrição':r.produto,
                'Quantidade':r.estoque,'Lote Indústria':r.lote_ind,'Local':r.local,'Setor':r.setor,
                'Data de Vencimento':r.vencimento,'Dias a Vencer':r.dias,
                'Meses a Vencer':meses,'Criticidade':r.urgencia};
      }
    });
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows.length?rows:[{}]), fam.nome);
  });
  // Aba Em Processo: registros com Setor Doca/Packing; Família na 1a coluna
  var emProcesso = DATA.saldo_completo.filter(function(r){ return _proc(r.setor); }).map(function(r){
    var meses=(r.dias!==null&&r.dias!==undefined)?Math.round(r.dias/30*10)/10:'';
    return {'Família':r.familia,'SKU':r.sku,'Descrição':r.produto,
            'Quantidade':r.estoque,'Lote Indústria':r.lote_ind,'Local':r.local,'Setor':r.setor,
            'Data de Vencimento':r.vencimento,'Dias a Vencer':r.dias,
            'Meses a Vencer':meses,'Criticidade':r.urgencia};
  });
  emProcesso.sort(function(a,b){return (a['Família']||'').localeCompare(b['Família']||'')||(''+a.SKU).localeCompare(''+b.SKU);});
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(emProcesso.length?emProcesso:[{}]), 'Em Processo');
  XLSX.writeFile(wb, 'Saldo_Completo_por_Familia.xlsx');
}
"""
if 'function exportarExcel' not in new_html:
    _ins = new_html.rfind('</script>')
    if _ins >= 0:
        new_html = new_html[:_ins] + _EXPORT_JS + new_html[_ins:]

import tempfile as _tf, shutil as _sh
_dir=os.path.dirname(HTML_PATH)
_ok=False
for _try in range(3):
    _fd,_tmpf=_tf.mkstemp(suffix='.html', dir=_dir)
    with os.fdopen(_fd,'w',encoding='utf-8') as f:
        f.write(new_html)
    with open(_tmpf,'r',encoding='utf-8') as f:
        _chk=f.read()
    if '</html>' in _chk and len(_chk)==len(new_html):
        _sh.move(_tmpf, HTML_PATH); _ok=True; break
    os.remove(_tmpf)
if not _ok:
    print("ERRO: falha ao gravar HTML integro apos 3 tentativas."); raise SystemExit(1)

print("[OK] Dashboard atualizado.")
print("  Familias: " + str(len(familia)) + " | Linhas PA: " + str(len({x['linha'] for x in pa_list})))
