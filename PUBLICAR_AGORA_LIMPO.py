"""
PUBLICAR_AGORA_LIMPO.py
Corrige git corrompido e publica no GitHub.
Duplo clique para executar.
"""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def run(cmd, capture=False):
    return subprocess.run(cmd, cwd=ROOT, capture_output=capture,
                          text=True, encoding='utf-8', errors='replace')

def runcap(cmd):
    r = run(cmd, capture=True)
    out = (r.stdout or '') + (r.stderr or '')
    return r.returncode, out.strip()

print("=" * 55)
print(" PUBLICANDO NO GITHUB - CORRECAO COMPLETA")
print("=" * 55)

# 1. Remover lock
lock = os.path.join(ROOT, '.git', 'index.lock')
if os.path.exists(lock):
    os.remove(lock)
    print("\n[1] index.lock removido.")
else:
    print("\n[1] Sem lock.")

# 2. Reconstruir index corrompido
print("\n[2] Reconstruindo index git...")
code, out = runcap(['git', 'read-tree', 'HEAD'])
print("   " + (out or "OK"))

# 3. Adicionar arquivos
print("\n[3] Adicionando arquivos...")
run(['git', 'add', '-A'])
run(['git', 'add', '-f', os.path.join('output', 'Analise_Estoque_GYP.xlsx')])
code, out = runcap(['git', 'diff', '--cached', '--name-only'])
print("   Arquivos prontos para commit:")
for f in out.splitlines():
    print("     - " + f)

# 4. Commit
print("\n[4] Commit...")
code, out = runcap(['git', 'commit', '-m', 'Exportar Excel + dashboard atualizado'])
print("   " + (out or "Nada para commitar."))

# 5. Push
print("\n[5] Push para GitHub...")
code, out = runcap(['git', 'push', 'origin', 'main'])
print("   " + out)
if code != 0:
    print("   Tentando force push...")
    code, out = runcap(['git', 'push', 'origin', 'main', '--force'])
    print("   " + out)

# 6. Resultado
print("\n" + "=" * 55)
code2, log = runcap(['git', 'log', '--oneline', '-3'])
print(" Ultimos commits:")
for l in log.splitlines():
    print("   " + l)
print()
if code == 0:
    print(" PRONTO! Aguarde 1-2 min e acesse:")
    print(" https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html")
else:
    print(" [AVISO] Verifique se ha erros acima.")
print("=" * 55)
input("\nPressione Enter para sair.")
