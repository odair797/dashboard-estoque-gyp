"""
ATUALIZACAO DIARIA - DASHBOARD & EXCEL DE ESTOQUE / YBERA GROUP
COMO USAR:
  1. Cole o .tsv do Senior (Saldo de Estoque) na pasta input/
  2. Rode:  python atualizar.py
  3. Saidas: output/Analise_Estoque_GYP.xlsx e Dashboard_Estoque_GYP.html
"""
import sys, os, glob, subprocess
from datetime import datetime

ROOT       = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(ROOT, 'input')
OUTPUT_DIR = os.path.join(ROOT, 'output')
SCRIPTS    = os.path.join(ROOT, 'scripts')

os.makedirs(INPUT_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 68)
print("  ATUALIZACAO DASHBOARD ESTOQUE - YBERA GROUP")
print("=" * 68)
print("  Data/hora: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
print()

tsvs = glob.glob(os.path.join(INPUT_DIR, '*.tsv')) + glob.glob(os.path.join(INPUT_DIR, '*.txt'))
if not tsvs:
    print("ERRO: nenhum arquivo .tsv encontrado em input/")
    print("   Coloque o arquivo exportado do Senior em: " + INPUT_DIR)
    sys.exit(1)

COL_OBRIGATORIA = 'Data de Vencimento'

def eh_saldo_estoque(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
            cabecalho = fh.readline()
        return COL_OBRIGATORIA in cabecalho.split('\t')
    except Exception:
        return False

tsv_path = None
ignorados = []
for cand in sorted(tsvs, key=os.path.getmtime, reverse=True):
    if eh_saldo_estoque(cand):
        tsv_path = cand
        break
    ignorados.append(os.path.basename(cand))

if tsv_path is None:
    print("ERRO: nenhum TSV de SALDO DE ESTOQUE encontrado em input/.")
    print("   Os arquivos precisam conter a coluna '" + COL_OBRIGATORIA + "'.")
    if ignorados:
        print("   Arquivos ignorados (outro tipo de exportacao):")
        for nome in ignorados:
            print("     - " + nome)
    print("   Exporte o relatorio de Saldo de Estoque no Senior e tente de novo.")
    sys.exit(1)

if ignorados:
    print("[AVISO] Arquivos ignorados (nao sao Saldo de Estoque):")
    for nome in ignorados:
        print("   - " + nome)

print("Arquivo de entrada: " + os.path.basename(tsv_path))
print("Pasta de saida    : output/")
print()

print("--- Etapa 1/2: Gerando Excel ---")
_env = os.environ.copy(); _env['PYTHONIOENCODING'] = 'utf-8'
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'processar_estoque.py'), tsv_path],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', env=_env)
print(r.stdout or '')
if r.returncode != 0:
    print("ERRO em processar_estoque.py:")
    print(r.stderr[:1500])
    sys.exit(1)

print("--- Etapa 2/2: Atualizando Dashboard HTML ---")
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'build_dashboard.py')],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', env=_env)
print(r.stdout or '')
if r.returncode != 0:
    print("[AVISO] em build_dashboard.py:")
    print(r.stderr[:800])

print()
print("=" * 68)
print("  ATUALIZACAO CONCLUIDA")
print("=" * 68)
print("   Excel    : output/Analise_Estoque_GYP.xlsx")
print("   Dashboard: Dashboard_Estoque_GYP.html")
print("=" * 68)
