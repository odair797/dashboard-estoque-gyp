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
# Setores "em processo"/indisponiveis: DOCA, PACKING, AVARIA/BLOQUEADOS, REPROVADO.
# Esses PA nao contam no compilado nem no grafico por linha.
_setor_pa = pa_df.get('Setor', pd.Series('', index=pa_df.index)).astype(str)
_excluir = 'DOCA|PACKING|AVARIA|BLOQUEAD|REPROVAD'
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
