# -*- coding: utf-8 -*-
"""Deixa o nome da familia e os valores do grafico 'Estoque Ativo por Familia'
em PRETO (#1A1714). Roda no Python local (sem mount), com guarda anti-truncamento,
e publica em seguida."""
import os, re, sys, subprocess, tempfile, shutil
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, 'Dashboard_Estoque_GYP.html')

s = open(HTML, encoding='utf-8').read()
if '</html>' not in s or 'const DATA' not in s:
    print('ERRO: HTML lido parece truncado/invalido. Nada foi alterado.'); input('Enter para sair...'); sys.exit(1)

m = re.search(r"new Chart\(document\.getElementById\('chartFamilia'\),\{.*?\}\}\);", s, re.DOTALL)
if not m:
    print('ERRO: bloco chartFamilia nao encontrado.'); input('Enter para sair...'); sys.exit(1)

bloco = m.group(0)
n = bloco.count("'#E2DCCB'")
print('Ocorrencias de cor creme (#E2DCCB) no chartFamilia:', n)
novo = bloco.replace("'#E2DCCB'", "'#1A1714'")
s2 = s[:m.start()] + novo + s[m.end():]

if '</html>' not in s2 or len(s2) < len(s) - 50:
    print('ERRO pos-edicao: resultado invalido. Abortado.'); input('Enter para sair...'); sys.exit(1)

fd, tmp = tempfile.mkstemp(suffix='.html', dir=ROOT)
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(s2)
chk = open(tmp, encoding='utf-8').read()
if '</html>' in chk and len(chk) == len(s2):
    shutil.move(tmp, HTML)
    print('OK: nome da familia e valores agora em PRETO. Trocas:', n)
else:
    os.remove(tmp); print('ERRO ao gravar arquivo integro. Abortado.'); input('Enter para sair...'); sys.exit(1)

print('Publicando no GitHub...')
subprocess.run([sys.executable, os.path.join(ROOT, 'publicar.py')], cwd=ROOT)
print('Concluido.')
