"""
PUBLICAR.PY - commit/push do dashboard no GitHub e abrir no Chrome.
- Le/grava .github_config.txt (REPO_URL e PAGES_URL).
- A PAGES_URL e derivada AUTOMATICAMENTE da REPO_URL.
- So pede a URL do repositorio na 1a vez.
"""
import os, sys, re, subprocess, webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG  = os.path.join(ROOT, '.github_config.txt')
ARQUIVO_DASH = 'Dashboard_Estoque_GYP.html'

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, text=True, encoding='utf-8',
                          errors='replace', **kw)

def ler_cfg():
    d = {}
    if os.path.exists(CFG):
        for ln in open(CFG, encoding='utf-8'):
            if '=' in ln:
                k, v = ln.strip().split('=', 1)
                d[k.upper()] = v
    return d

def gravar_cfg(repo, pages):
    with open(CFG, 'w', encoding='utf-8') as f:
        f.write("REPO_URL=" + repo + "\n")
        f.write("PAGES_URL=" + pages + "\n")

def derivar_pages(repo_url):
    """https://github.com/USER/REPO(.git) -> https://USER.github.io/REPO/arquivo"""
    u = repo_url.strip().rstrip('/')
    u = re.sub(r'\.git$', '', u)
    m = re.search(r'github\.com[:/]+([^/]+)/(.+)$', u)
    if not m:
        return ''
    user, repo = m.group(1), m.group(2)
    return "https://{}.github.io/{}/{}".format(user, repo, ARQUIVO_DASH)

def main():
    cfg = ler_cfg()
    repo_url  = cfg.get('REPO_URL', '').strip()
    pages_url = cfg.get('PAGES_URL', '').strip()

    git_dir = os.path.join(ROOT, '.git')
    primeira = not os.path.isdir(git_dir)

    if not repo_url:
        print("=" * 60)
        print(" CONFIGURACAO INICIAL DO GITHUB (so nesta primeira vez)")
        print("=" * 60)
        print(" Crie um repositorio VAZIO em https://github.com/new")
        print(" - NAO marque 'Add a README'")
        print(" - Marque Public (para o Pages gratis)")
        print()
        repo_url = input(" Cole a URL do repositorio (.git): ").strip().strip('"')
        if not repo_url:
            print(" URL vazia. Saindo.")
            sys.exit(1)

    # Pages SEMPRE derivada automaticamente da URL do repo
    pages_url = derivar_pages(repo_url) or pages_url
    gravar_cfg(repo_url, pages_url)
    print(" Link publico (GitHub Pages):")
    print("   " + pages_url)
    print()

    if primeira:
        run(['git', 'init', '-b', 'main'], capture_output=True)
        run(['git', 'config', 'user.email', 'odair-matos52@hotmail.com'])
        run(['git', 'config', 'user.name', 'Odair'])
        run(['git', 'remote', 'remove', 'origin'], capture_output=True)
        run(['git', 'remote', 'add', 'origin', repo_url], capture_output=True)
    else:
        # garante que o remoto aponta para a URL configurada
        run(['git', 'remote', 'set-url', 'origin', repo_url], capture_output=True)

    print(" Enviando para o GitHub...")
    # Força inclusão do Excel mesmo que ainda esteja em cache do .gitignore
    xlsx = os.path.join(ROOT, 'output', 'Analise_Estoque_GYP.xlsx')
    if os.path.exists(xlsx):
        run(['git', 'add', '-f', xlsx], capture_output=True)
    run(['git', 'add', '-A'], capture_output=True)
    st = run(['git', 'status', '--porcelain'], capture_output=True)
    if (st.stdout or '').strip():
        run(['git', 'commit', '-m', 'Atualizacao dashboard'], capture_output=True)
        print("   Commit criado.")
    else:
        print("   Nada novo para commitar.")

    push = run(['git', 'push', '-u', 'origin', 'main'], capture_output=True)
    if push.returncode != 0:
        # Remoto pode ja ter conteudo (ex.: README). Para um repo de
        # dashboard gerado automaticamente, sobrescrever e seguro.
        push = run(['git', 'push', '-u', 'origin', 'main', '--force'], capture_output=True)
    if push.returncode != 0:
        print()
        print(" [ERRO] Falha no push:")
        print((push.stderr or push.stdout or '')[:600])
        print()
        print(" LOGIN DO GITHUB NECESSARIO (so na primeira vez):")
        print(" - Ao rodar, abre uma janelinha do GitHub (Git Credential")
        print("   Manager). Clique em 'Sign in with your browser' e")
        print("   autorize com a sua conta odair797.")
        print(" - Depois disso fica salvo e nunca mais pede.")
        print(" - Alternativa: instalar o GitHub Desktop e logar uma vez.")
        sys.exit(1)
    print("   Publicado com sucesso.")
    print()

    # Abrir no Chrome
    print(" Abrindo no Chrome...")
    abriu = False
    for caminho in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.exists(caminho):
            subprocess.Popen([caminho, pages_url])
            abriu = True
            break
    if not abriu:
        webbrowser.open(pages_url)
    print("   " + pages_url)
    print()
    print(" Obs.: o GitHub Pages pode levar 1-2 min para refletir.")
    print("       Se nao mudar, recarregue com Ctrl+F5.")

if __name__ == '__main__':
    main()
