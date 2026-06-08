"""
PATCH_EXPORTAR.py
1. Baixa o HTML atual do GitHub Pages
2. Substitui a função exportarSaldoCompleto pela versão com 6 abas + Em Processo
3. Salva na pasta _sistema para upload
"""
import os, re, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, 'Dashboard_Estoque_GYP.html')
URL  = 'https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html'

NOVA_FUNCAO = """function exportarSaldoCompleto() {
  var wb = XLSX.utils.book_new();
  var familias = [
    {key:'Produto Acabado', nome:'Produto Acabado', comLinha:true},
    {key:'Materia Prima',   nome:'Materia Prima',   comLinha:false},
    {key:'Embalagem',       nome:'Embalagem',        comLinha:false},
    {key:'Granel',          nome:'Granel',           comLinha:false},
    {key:'Apoio',           nome:'Apoio',            comLinha:false},
  ];
  familias.forEach(function(fam) {
    var dados = DATA.saldo_completo.filter(function(r){
      var rf=r.familia?r.familia.replace(/[\\u00e1\\u00e0\\u00e3]/g,'a').replace(/[\\u00e9\\u00ea]/g,'e').replace(/[\\u00ed]/g,'i').replace(/[\\u00f3\\u00f4]/g,'o').replace(/[\\u00fa]/g,'u').toLowerCase():'';
      var kf=fam.key.replace(/[\\u00e1\\u00e0\\u00e3]/g,'a').replace(/[\\u00e9\\u00ea]/g,'e').replace(/[\\u00ed]/g,'i').replace(/[\\u00f3\\u00f4]/g,'o').replace(/[\\u00fa]/g,'u').toLowerCase();
      return rf===kf;
    });
    var rows = dados.map(function(r) {
      var meses=(r.dias!==null&&r.dias!==undefined)?Math.round(r.dias/30*10)/10:'';
      if (fam.comLinha) {
        return {'Linha':r.linha,'SKU':r.sku,'Descricao':r.produto,'Quantidade':r.estoque,
                'Lote Industria':r.lote_ind,'Local':r.local,'Data de Vencimento':r.vencimento,
                'Dias a Vencer':r.dias,'Meses a Vencer':meses,'Criticidade':r.urgencia};
      } else {
        return {'SKU':r.sku,'Descricao':r.produto,'Quantidade':r.estoque,
                'Lote Industria':r.lote_ind,'Local':r.local,'Data de Vencimento':r.vencimento,
                'Dias a Vencer':r.dias,'Meses a Vencer':meses,'Criticidade':r.urgencia};
      }
    });
    XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(rows.length?rows:[{}]),fam.nome);
  });
  var emProcesso = DATA.saldo_completo.filter(function(r){
    return r.local==='00000348'||r.local==='00004569'||r.local==='00000349';
  }).map(function(r){
    var meses=(r.dias!==null&&r.dias!==undefined)?Math.round(r.dias/30*10)/10:'';
    return {'Status':r.local==='00000348'?'Finalizado':'Em Separacao',
            'Local':r.local,'SKU':r.sku,'Descricao':r.produto,'Familia':r.familia,
            'Quantidade':r.estoque,'Lote Industria':r.lote_ind,
            'Data de Vencimento':r.vencimento,'Dias a Vencer':r.dias,
            'Meses a Vencer':meses,'Criticidade':r.urgencia};
  });
  emProcesso.sort(function(a,b){return a.Status.localeCompare(b.Status);});
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(emProcesso.length?emProcesso:[{}]),'Em Processo');
  XLSX.writeFile(wb,'Saldo_Completo_por_Familia.xlsx');
}"""

print("="*55)
print(" CORRIGINDO FUNÇÃO DE EXPORTAR")
print("="*55)

print("\n[1] Baixando HTML do GitHub Pages...")
try:
    with urllib.request.urlopen(URL, timeout=30) as r:
        content = r.read().decode('utf-8', errors='replace')
    print(f"  Baixado: {len(content):,} chars")
except Exception as e:
    print(f"  Falha ao baixar. Usando arquivo local...")
    content = open(HTML, 'r', encoding='utf-8', errors='replace').read()
    # Normalizar \r
    content = re.sub(r'\r+', '\n', content)
    print(f"  Local: {len(content):,} chars")

print("\n[2] Localizando função antiga...")
# Encontrar início da função
idx_ini = content.find('function exportarSaldoCompleto')
if idx_ini < 0:
    print("  [ERRO] Função não encontrada!")
    input("Enter para sair.")
    raise SystemExit(1)

# Encontrar fim da função (próximo }\n que fecha a função raiz)
depth = 0
idx_fim = idx_ini
for i in range(idx_ini, len(content)):
    if content[i] == '{':
        depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0:
            idx_fim = i + 1
            break

print(f"  Encontrada: pos {idx_ini} até {idx_fim} ({idx_fim-idx_ini} chars)")

print("\n[3] Substituindo função...")
content = content[:idx_ini] + NOVA_FUNCAO + content[idx_fim:]

ok = 'Em Processo' in content and 'Em Separacao' in content
print(f"  Em Processo: {'OK' if ok else 'FALHOU'}")

print("\n[4] Salvando...")
with open(HTML, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print(f"  Salvo: {len(content):,} chars")

print("\n" + "="*55)
if ok:
    print(" PRONTO! Arquivo corrigido e salvo.")
    print(" O upload para GitHub será feito automaticamente.")
else:
    print(" [ERRO] Verificação falhou.")
print("="*55)
input("\nPressione Enter para sair.")
