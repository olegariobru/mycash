# Clareza Financeira

Aplicativo desktop para Windows, criado em Python, para controlar uma meta mensal, registrar despesas e arquivar DANFEs, notas fiscais e comprovantes. Não usa navegador, servidor ou conta online.

## Executar

Para gerar localmente, execute `build_exe.bat` e depois abra `dist/Clareza Financeira.exe`. No GitHub, a automação **Build Windows** também disponibiliza o executável na área de artefatos da execução. Na primeira abertura, o programa cria sua pasta local de dados.

## O que cada parte faz

### `desktop.py`

É o código-fonte principal e contém quatro camadas:

1. **Persistência:** cria e acessa o banco SQLite `consultoria.db`.
2. **Regras financeiras:** converte valores brasileiros, calcula total gasto, saldo e percentual da meta.
3. **Interface:** monta os cards, o formulário, a tabela de lançamentos e as janelas de confirmação.
4. **Movimento:** anima a abertura da janela, revela os cards em cascata e faz os valores contarem de zero até o resultado.

### `dados/`

Criada automaticamente ao lado do `.exe`:

- `consultoria.db`: metas e lançamentos.
- `anexos/`: cópias das notas e comprovantes selecionados.

Ao excluir um lançamento, seu anexo também é removido. Para fazer backup, copie a pasta `dados` inteira.

### `assets/fonts/`

Recebe as fontes incorporadas ao executável. Elas são baixadas automaticamente por `scripts/download_fonts.py` durante o build:

- **Montserrat:** títulos, números e botões.
- **Roboto:** textos, campos e tabela.

Assim, o visual não depende das fontes instaladas no Windows.

### `build_exe.bat`

Cria o ambiente Python, instala PyInstaller e PySide6 6.8.3 e recompila o executável. O resultado fica em `dist/Clareza Financeira.exe`.

### `dist/`

Contém a versão pronta para uso. O `.exe` inclui Python, interface gráfica, fontes e dependências.

## Recursos

- Meta mensal editável.
- Resumo de gasto, saldo e utilização da meta.
- Lançamentos por data, categoria e fornecedor.
- Observações e anexos PDF, PNG, JPG, JPEG ou WEBP de até 12 MB.
- Abertura do comprovante com duplo clique ou botão.
- Exclusão com confirmação.
- Dados locais em SQLite.
- Entrada em cascata, fade suave e contadores animados com `ease-out`.

## Motion design

Os movimentos seguem a [AI Motion Library](https://github.com/apenasdouglas/ai-motion-library): `fade in`, `stagger`, `count-up` e curvas suaves. Em um sistema financeiro, as animações foram mantidas curtas e funcionais para não prejudicar a leitura.

## Desenvolvimento

Requisitos: Python 3.11 ou 3.12.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install PySide6==6.8.3 pyinstaller
python desktop.py
```

Para validar o pacote sem abrir a janela:

```powershell
dist\Clareza Financeira.exe --self-test
```

## Licenças

- Roboto e Montserrat: SIL Open Font License.
- AI Motion Library: MIT; utilizada como referência de motion design.
- Demais componentes: consulte `THIRD_PARTY_NOTICES.md`.

> Ferramenta de organização financeira; não substitui orientação contábil ou financeira profissional.

