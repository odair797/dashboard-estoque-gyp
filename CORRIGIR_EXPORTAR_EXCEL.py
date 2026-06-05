"""
CORRIGIR_EXPORTAR_EXCEL.py
- Remove bytes nulos do HTML (corrompido pelo sandbox)
- Garante que as funções de exportar Excel estão presentes
- Salva arquivo limpo
"""
import os, re, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
HTML   = os.path.join(ROOT, 'Dashboard_Estoque_GYP.html')
MODELO = os.path.join(ROOT, '_ARQUIVO_nao_usar', '_MODELO_Dashboard_Estoque_GYP.html')

EXPORT_JS = """
// ========== FUNÇÕES DE EXPORTAÇÃO EXCEL ==========
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
  var rows = DATA.saldo_completo.map(function(r) {
    return {'Local':r.local,'SKU':r.sku,'Produto':r.produto,'Família':r.familia,
            'Unidade':r.unidade,'Linha':r.linha,'Setor':r.setor,'Lote':r.lote,
            'Lote Indústria':r.lote_ind,'Estoque':r.estoque,
            'Vencimento':r.vencimento,'Dias':r.dias,'Criticidade':r.urgencia};
  });
  _xlsxDownload(rows, 'Saldo_Completo.xlsx');
}
"""

print("=" * 55)
print(" CORRIGINDO DASHBOARD...")
print("=" * 55)

# 1. Ler HTML atual em binário e remover bytes nulos
print(f"\n[1/4] Lendo: {HTML}")
raw = open(HTML, 'rb').read()
null_count = raw.count(b'\x00')
if null_count:
    print(f"      Removendo {null_count} bytes nulos...")
    raw = raw.replace(b'\x00', b'')
content = raw.decode('utf-8', errors='replace')
print(f"      Tamanho limpo: {len(content):,} chars")

# 2. Verificar integridade mínima
print("\n[2/4] Verificando integridade...")
if 'const DATA' not in content or '</html>' not in content:
    print("      HTML inválido. Usando modelo de backup...")
    if not os.path.exists(MODELO):
        print(f"[ERRO] Modelo não encontrado: {MODELO}")
        input("Pressione Enter para sair.")
        raise SystemExit(1)
    content = open(MODELO, 'r', encoding='utf-8', errors='replace').read()
    print("      Modelo carregado.")
else:
    print("      OK — DATA e </html> presentes.")

# 3. Remover funções antigas se existirem (evitar duplicata)
print("\n[3/4] Injetando funções de exportação...")
if 'function exportarExcel' in content:
    print("      Funções existem — substituindo...")
    content = re.sub(
        r'// ={5,} FUN.*?EXCEL ={5,}[\s\S]*?(?=\n</script>)',
        '',
        content
    )

insert_pos = content.rfind('</script>')
if insert_pos < 0:
    print("[ERRO] Não encontrou </script> no HTML.")
    input("Pressione Enter para sair.")
    raise SystemExit(1)

content = content[:insert_pos] + EXPORT_JS + content[insert_pos:]
print("      Funções inseridas.")

# 4. Salvar
print("\n[4/4] Salvando...")
shutil.copy2(HTML, HTML + '.bak')
with open(HTML, 'w', encoding='utf-8') as f:
    f.write(content)

# Verificar resultado
final = open(HTML, 'rb').read()
nulls = final.count(b'\x00')
fns_ok = all(fn in content for fn in ['function exportarExcel', 'function exportarVencidos', 'function exportarSaldoCompleto'])

print(f"\n{'='*55}")
print(f" Bytes nulos: {nulls}")
print(f" Funções exportar: {'OK' if fns_ok else 'FALHOU'}")
print(f" Tamanho final: {len(final):,} bytes")
print(f"{'='*55}")

if nulls == 0 and fns_ok:
    print("\n PRONTO! Abra o Dashboard no navegador e teste os botões.")
    print(" Depois rode: PUBLICAR_EXCEL_GITHUB.bat")
else:
    print("\n[AVISO] Algo pode ter dado errado. Verifique acima.")

input("\nPressione Enter para sair.")
