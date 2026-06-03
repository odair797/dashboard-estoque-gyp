# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
  WATCHER — Atualiza o dashboard automaticamente ao baixar novo TSV
═══════════════════════════════════════════════════════════════════════════

Monitora a pasta input/ (e opcionalmente Downloads) a cada 3 segundos.
Quando detecta um novo arquivo .tsv que ainda não foi processado,
dispara o atualizar.py automaticamente.

Uso:
    Duplo-clique em INICIAR_WATCHER.bat
    OU rode no terminal: python watcher.py

Para parar: feche a janela do terminal (Ctrl+C também funciona).
═══════════════════════════════════════════════════════════════════════════
"""
import os, sys, glob, time, shutil, subprocess
from datetime import datetime
from pathlib import Path

ROOT       = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(ROOT, 'input')
DOWNLOADS  = os.path.join(Path.home(), 'Downloads')
ATUALIZAR  = os.path.join(ROOT, 'atualizar.py')
INTERVAL   = 3  # segundos entre checagens

# Padrões de arquivos a monitorar (case-insensitive, qualquer um)
PATTERNS = ['*.tsv', '*Exportacao*.txt', '*Saldo*.txt']

os.makedirs(INPUT_DIR, exist_ok=True)

def log(msg, color='37'):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\033[90m[{ts}]\033[0m \033[{color}m{msg}\033[0m", flush=True)

def list_tsvs(folder):
    files = []
    for p in PATTERNS:
        files += glob.glob(os.path.join(folder, p))
    return {os.path.basename(f): os.path.getmtime(f) for f in files}

def banner():
    print()
    print("\033[33m" + "═" * 68 + "\033[0m")
    print("\033[33m  WATCHER ATIVO — YBERA GROUP / Saldo de Estoque\033[0m")
    print("\033[33m" + "═" * 68 + "\033[0m")
    print(f"  📂 Monitorando : {INPUT_DIR}")
    print(f"  📥 E também   : {DOWNLOADS}")
    print(f"  🔄 Intervalo  : {INTERVAL}s")
    print()
    print("  Cole o .tsv em uma dessas pastas e o dashboard atualizará sozinho.")
    print("  Para parar: feche esta janela ou pressione Ctrl+C")
    print("\033[33m" + "═" * 68 + "\033[0m")
    print()

def rodar_atualizar():
    log("→ Disparando atualizar.py ...", '36')
    r = subprocess.run([sys.executable, ATUALIZAR], cwd=ROOT)
    if r.returncode == 0:
        log("✓ Dashboard e Excel atualizados.", '32')
    else:
        log(f"⚠ Erro (returncode={r.returncode})", '31')
    print()

def main():
    banner()

    # Snapshot inicial
    seen_input = list_tsvs(INPUT_DIR)
    seen_down  = list_tsvs(DOWNLOADS)
    log(f"Snapshot inicial: {len(seen_input)} no input/, {len(seen_down)} em Downloads/")
    log("Aguardando novos arquivos...")
    print()

    while True:
        try:
            time.sleep(INTERVAL)

            # 1) Verificar Downloads (copiar pra input/ se houver TSV novo)
            atual_down = list_tsvs(DOWNLOADS)
            novos_down = {k:v for k,v in atual_down.items() if k not in seen_down or v > seen_down.get(k, 0)}
            for nome, _mt in novos_down.items():
                src = os.path.join(DOWNLOADS, nome)
                dst = os.path.join(INPUT_DIR, nome)
                # ignorar arquivos sendo escritos (size 0 ou crescendo)
                try:
                    sz1 = os.path.getsize(src); time.sleep(0.6)
                    sz2 = os.path.getsize(src)
                    if sz1 == 0 or sz1 != sz2:
                        continue  # ainda está sendo baixado
                except FileNotFoundError:
                    continue
                log(f"📥 Detectado novo arquivo no Downloads: {nome}", '36')
                try:
                    shutil.copy2(src, dst)
                    log(f"   Copiado → input/{nome}", '32')
                except Exception as e:
                    log(f"   ⚠ Falha ao copiar: {e}", '31')
                    continue
            seen_down = atual_down

            # 2) Verificar input/ (rodar se houver TSV novo)
            atual_input = list_tsvs(INPUT_DIR)
            novos_input = {k:v for k,v in atual_input.items() if k not in seen_input or v > seen_input.get(k, 0)}
            if novos_input:
                for nome in novos_input:
                    log(f"📄 Novo TSV em input/: {nome}", '36')
                rodar_atualizar()
                seen_input = list_tsvs(INPUT_DIR)
                log("Aguardando próximo arquivo...")
                print()

        except KeyboardInterrupt:
            print()
            log("Watcher encerrado pelo usuário.", '33')
            break
        except Exception as e:
            log(f"Erro inesperado: {e}", '31')
            time.sleep(5)

if __name__ == '__main__':
    main()
