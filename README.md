# PPGFIS DFT Plotter - Versão de testes

O PPFIS-DFT-PLOTTER é um Software, de código aberto, disponibilizado com intuito de facilitar a produtividade dos estudantes que desejam visualizar os resultados obtidos no pacote DFT - Quantum Espresso.

Este software não possui fins lucrativos, sendo assim, **NÃO LUCRE COM ESTE SOFTWARE**.

## Instalação

Requer Python 3.10 ou superior. Na pasta do projeto:

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python executar.py
```

Alternativamente: `python -m ppgfis_plotter`.

## Organização

| Arquivo | Responsabilidade |
|---|---|
| `executar.py` | Inicialização simples |
| `ppgfis_plotter/common.py` | Bibliotecas e configurações globais |
| `ppgfis_plotter/readers.py` | Leitura dos arquivos de bandas, DOS e PDOS do Quantum ESPRESSO |
| `ppgfis_plotter/analysis.py` | Gap, bordas de bandas e tratamento numérico |
| `ppgfis_plotter/exports.py` | Exportação dos resultados eletrônicos |
| `ppgfis_plotter/plotting.py` | Canvas Matplotlib, ferramentas de curvas e formatação |
| `ppgfis_plotter/ui_helpers.py` | Componentes auxiliares da interface |
| `ppgfis_plotter/home.py` | Página inicial |
| `ppgfis_plotter/bands.py` | Aba Estrutura de Bandas |
| `ppgfis_plotter/dos.py` | Aba DOS |
| `ppgfis_plotter/pdos.py` | Aba PDOS |
| `ppgfis_plotter/profiles.py` | Perfis de aparência |
| `ppgfis_plotter/window.py` | Janela principal e navegação |

## Notas

- Preferências do usuário são armazenadas na pasta do projeto, como na versão de teste.
- Recomenda-se validar as abas Bandas, DOS e PDOS com arquivos reais antes de distribuir a terceiros.
- Para distribuir um executável sem Python, é necessária uma etapa adicional de empacotamento (por exemplo, PyInstaller), não incluída neste ZIP.
# PPGFIS-DFT-Plotter
