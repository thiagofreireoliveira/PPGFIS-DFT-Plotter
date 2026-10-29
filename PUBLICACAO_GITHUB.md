# Publicação do PPGFIS DFT Plotter no GitHub

## Antes de publicar

1. Revise direitos autorais, autoria, nomes institucionais e logotipos.
2. Teste o programa com dados reais do Quantum ESPRESSO e com nspin=1 e nspin=2.
3. Escolha uma licença: MIT (permite uso comercial) ou outra licença adequada à intenção do projeto. **Este pacote ainda não inclui licença.**
4. Confira README.md e requirements.txt.

## Criar repositório

Acesse https://github.com/new e crie um repositório público chamado `PPGFIS-DFT-Plotter`. Não marque a opção de adicionar README se ele já existe localmente.

## Enviar

Na pasta que contém executar.py:

```bash
git init
git add .
git commit -m "Publicacao inicial do PPGFIS DFT Plotter"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/PPGFIS-DFT-Plotter.git
git push -u origin main
```

## Atualizar

```bash
git add .
git commit -m "Descricao da atualizacao"
git push
```

## Criar uma versão

No GitHub, acesse Releases > Draft a new release e publique uma versão após validação funcional.
