"""
ATUALIZAR_E_PUBLICAR.py
1. Corrige git (remove lock + recria index corrompido)
2. Regenera o dashboard
3. Publica no GitHub
"""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def cap(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()

print("=" * 55)
print(" CORRIGIR GIT + PUBLICAR NO GITHUB")
print("=" * 55)

# ── 1. Corrigir git ───────────────────────────────────────
print("\n[1/4] Corrigindo git...")

# Remover lock
lock = os.path.join(ROOT, '.git', 'index.lock')
if os.path.exists(lock):
    os.remove(lock)
    print("  index.lock removido.")

# Remover index corrompido e recriar
idx = os.path.join(ROOT, '.git', 'index')
if os.path.exists(idx):
    os.remove(idx)
    print("  index corrompido removido.")

# Recriar index a partir do HEAD
code, out = cap(['git', 'reset', 'HEAD'])
if code != 0:
    code, out = cap(['git', 'read-tree', 'HEAD'])
print("  Index recriado: " + (out or "OK"))

# ── 2. Regenerar dashboard ────────────────────────────────
print("\n[2/4] Regenerando dashboard...")
r = subprocess.run([sys.executable, 'atualizar.py'], cwd=ROOT,
                   encoding='utf-8', errors='replace')
print("  " + ("OK" if r.returncode == 0 else "Aviso: verifique erros acima"))

# ── 3. Adicionar arquivos ─────────────────────────────────
print("\n[3/4] Preparando commit...")
cap(['git', 'add', '-A'])
cap(['git', 'add', '-f', os.path.join('output', 'Analise_Estoque_GYP.xlsx')])

code, files = cap(['git', 'diff', '--cached', '--name-only'])
if files:
    print("  Arquivos:")
    for f in files.splitlines()[:10]:
        print("    - " + f)
    cap(['git', 'commit', '-m', 'Dashboard: exportar Excel 6 abas + Em Processo'])
    print("  Commit criado.")
else:
    print("  Nada novo — forçando re-add do HTML...")
    cap(['git', 'add', '-f', 'Dashboard_Estoque_GYP.html'])
    code2, files2 = cap(['git', 'diff', '--cached', '--name-only'])
    if files2:
        cap(['git', 'commit', '-m', 'Dashboard: exportar Excel 6 abas + Em Processo'])
        print("  Commit criado com HTML.")

# ── 4. Push ───────────────────────────────────────────────
print("\n[4/4] Publicando no GitHub...")
code, out = cap(['git', 'push', 'origin', 'main'])
if code != 0:
    print("  Force push...")
    code, out = cap(['git', 'push', 'origin', 'main', '--force'])
print("  " + (out.splitlines()[-1] if out else ""))

# ── Resultado ─────────────────────────────────────────────
print("\n" + "=" * 55)
_, log = cap(['git', 'log', '--oneline', '-3'])
for l in log.splitlines():
    print("  " + l)
print()
if code == 0:
    print(" PRONTO! Aguarde 1-2 min e teste:")
    print(" https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html")
else:
    print(" [ERRO] Push falhou. Resultado:")
    print(" " + out[:300])
print("=" * 55)
input("\nPressione Enter para sair.")
