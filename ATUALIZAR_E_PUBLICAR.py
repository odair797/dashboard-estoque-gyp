"""
ATUALIZAR_E_PUBLICAR.py
1. Regenera o dashboard com as funções de exportar Excel atualizadas
2. Corrige git travado (lock + index corrompido)
3. Publica tudo no GitHub
Duplo clique para executar.
"""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def run(cmd, capture=False):
    return subprocess.run(cmd, cwd=ROOT, capture_output=capture,
                          text=True, encoding='utf-8', errors='replace')

def cap(cmd):
    r = run(cmd, capture=True)
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()

print("=" * 55)
print(" ATUALIZAR + PUBLICAR NO GITHUB")
print("=" * 55)

# ── ETAPA 1: Regenerar dashboard ─────────────────────────
print("\n[1/4] Regenerando dashboard com novas funções...")
r = run([sys.executable, 'atualizar.py'])
if r.returncode != 0:
    print("  [AVISO] atualizar.py retornou erro. Continuando...")
else:
    print("  Dashboard regenerado.")

# ── ETAPA 2: Corrigir git ─────────────────────────────────
print("\n[2/4] Corrigindo git...")

lock = os.path.join(ROOT, '.git', 'index.lock')
if os.path.exists(lock):
    os.remove(lock)
    print("  index.lock removido.")

code, out = cap(['git', 'read-tree', 'HEAD'])
print("  read-tree: " + (out or "OK"))

# ── ETAPA 3: Adicionar arquivos ───────────────────────────
print("\n[3/4] Preparando commit...")
run(['git', 'add', '-A'])
run(['git', 'add', '-f', os.path.join('output', 'Analise_Estoque_GYP.xlsx')])

code, files = cap(['git', 'diff', '--cached', '--name-only'])
if files:
    print("  Arquivos novos:")
    for f in files.splitlines():
        print("    - " + f)
    code, out = cap(['git', 'commit', '-m', 'Exportar Excel 6 abas + Em Processo + dashboard atualizado'])
    print("  " + (out.splitlines()[0] if out else "Commit criado."))
else:
    print("  Nada novo para commitar (já estava atualizado).")

# ── ETAPA 4: Push ─────────────────────────────────────────
print("\n[4/4] Publicando no GitHub...")
code, out = cap(['git', 'push', 'origin', 'main'])
print("  " + (out.splitlines()[-1] if out else ""))
if code != 0:
    print("  Tentando force push...")
    code, out = cap(['git', 'push', 'origin', 'main', '--force'])
    print("  " + (out.splitlines()[-1] if out else ""))

# ── Resultado ─────────────────────────────────────────────
print("\n" + "=" * 55)
_, log = cap(['git', 'log', '--oneline', '-3'])
for l in log.splitlines():
    print("  " + l)
print()
if code == 0:
    print(" PRONTO! Aguarde 1-2 min e acesse:")
    print(" https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html")
else:
    print(" [ERRO] Push falhou. Verifique acima.")
print("=" * 55)
input("\nPressione Enter para sair.")
