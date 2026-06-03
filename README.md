# Dashboard Saldo de Estoque — YBERA GROUP

Sistema de análise diária de estoque a partir da exportação TSV do ERP Senior.
Gera automaticamente Excel com 5 abas e Dashboard HTML interativo.

## Como atualizar (uso diário)

**FLUXO COMPLETO — `PUBLICAR_NO_GITHUB.bat`** ⭐ (recomendado)

Faz tudo em 1 clique: atualiza → publica → abre no Chrome.

1. Arraste o `.tsv` baixado em cima do `PUBLICAR_NO_GITHUB.bat`
   (ou duplo-clique e cole o caminho)
2. Ele roda o `atualizar.py` (gera Excel + atualiza Dashboard)
3. Faz `git add`, `commit` e `push` pro GitHub automaticamente
4. Abre o Dashboard no Chrome usando o link público do GitHub Pages

Na **primeira execução** ele pergunta a URL do repositório e do GitHub Pages
(você precisa ter criado o repo no GitHub e ativado o Pages — instruções abaixo).

**Outros modos:**

- `ATUALIZAR_AGORA.bat` — só atualiza local, sem publicar
- `INICIAR_WATCHER.bat` — modo automático monitorando Downloads/
- Terminal: `python atualizar.py` — pega o .tsv mais recente em `input/`

## Estrutura

```
SALDO DE ESTOQUE/
├── ATUALIZAR_AGORA.bat             ← MANUAL — arraste o .tsv aqui
├── INICIAR_WATCHER.bat             ← AUTOMÁTICO — monitora Downloads/
├── PUBLICAR_NO_GITHUB.bat          ← publica/atualiza no GitHub
│
├── atualizar.py                    ← orquestrador (chamado pelos .bats)
├── watcher.py                      ← monitor automático
├── Dashboard_Estoque_GYP.html      ← abra este (atualizado a cada execução)
│
├── README.md
├── requirements.txt
├── input/                          ← TSV cai aqui
├── output/                         ← Excel gerado
├── docs/                           ← documentos auxiliares
└── scripts/
    ├── processar_estoque.py
    ├── build_excel_v9.py
    └── build_dashboard.py
```

## O que o Excel contém

5 abas no padrão **SKU · Descrição · Quantidade · Lote · Local · Vencimento · Dias · Meses · Criticidade**:

- 📦 **Produto Acabado** — agrupado por linha comercial (coluna Linha extra)
- 🧪 **Matéria Prima**
- 📦 **Embalagem**
- 🛢️ **Granel**
- 🔧 **Apoio**

Criticidade colorida: VENCIDO · CRÍTICO ≤60d · ATENÇÃO ≤120d · PRÓXIMO ≤180d · OK · SEM DATA.

## O que o Dashboard contém

4 abas:

- 🏠 **Resumo Executivo** — saldo por família + KPIs (SKUs, crítico, atenção, OK, vencidos) + gráficos
- ⏰ **Próximos de Vencer** — filtros por urgência/família, busca, exportar Excel
- 🔴 **Vencidos — Mover** — lista para mover ao setor [1102], exportar Excel
- 📦 **Compilado PA por Linha** — gráfico + tabela agrupada por linha, exportar Saldo Completo

## Configurar GitHub + Pages (uma vez só)

1. **Instale o Git**: https://git-scm.com/download/win
2. **Crie um repositório no GitHub**:
   - https://github.com/new
   - Nome: `saldo-estoque-ybera` (ou outro)
   - **NÃO** marque "Initialize this repository with a README"
   - **Public** (Pages grátis exige público) ou Private (Pages só com plano pago)
   - Clique em **Create repository**
   - Copie a URL: `https://github.com/seu-usuario/saldo-estoque-ybera.git`
3. **Ative o GitHub Pages**:
   - No repositório → **Settings** → **Pages**
   - Source: **Deploy from a branch**
   - Branch: **main** / **root** → **Save**
   - Aguarde 1-2 min. A URL pública será:
     `https://seu-usuario.github.io/saldo-estoque-ybera/Dashboard_Estoque_GYP.html`
4. **Arraste o TSV em cima do `PUBLICAR_NO_GITHUB.bat`** — ele pede as URLs na primeira vez e salva em `.github_config.txt`.

O `.gitignore` protege os TSVs e Excels (não vão pro GitHub).

## Dependências

```
pip install -r requirements.txt
```

(Python 3.10+ recomendado. Dependências: pandas, openpyxl, numpy.)

## Regras de negócio

- **Família** é definida pelo primeiro dígito do código do produto:
  - 1 → Matéria Prima
  - 2 → Embalagem
  - 3 → Granel
  - 4 → Produto Acabado
  - 5 → Apoio
- **Setor de vencidos**: `[1102] GYP - VENCIDOS (G9)` — itens vencidos fora desse setor entram na lista de "mover".
- **Limite "próximo de vencer"**: até 183 dias (≈ 6 meses).
