# QWEN.md

Guia de Deploy e Boas Práticas de Desenvolvimento

Este documento orienta como publicar e operar o pacote `buscador-de-cnpj` (servidor MCP) e descreve práticas recomendadas para desenvolvimento, testes e releases. Foi escrito pensando em agentes LLM (Qwen, Claude, etc.) e desenvolvedores humanos.

## Visão Geral

- Pacote PyPI: `buscador-de-cnpj`
- Entry point (CLI): `buscador-de-cnpj`
- Repositório: https://github.com/victortavernari/cnpj-mcp-server
- Requisitos: Python >= 3.11

## Autenticação (API Buscador de CNPJ)

- Header obrigatório: `x-api-key: <SUA_CHAVE>`
- Nunca envie a chave na query string. O cliente embutido já a injeta nos headers.
- Variáveis de ambiente suportadas (ordem de preferência): `CNPJ_API_KEY`, `CNPJ_API_TOKEN`, `BUSCADOR_CNPJ_API_KEY`, `API_KEY`.

Exemplos curl (ambiente local):
- Consulta detalhada: `curl -H "x-api-key: YOUR_API_KEY" "http://localhost:8001/cnpj/47271733000124"`
- Busca avançada: `curl -H "x-api-key: YOUR_API_KEY" "http://localhost:8001/search/?term=empresa"`

## Deploy

### Publicação no PyPI

Pré-requisitos:
- `~/.pypirc` configurado com credenciais do PyPI (usuário `__token__` + `password=pypi-...`) ou usar `uv publish --token ...`.
- `uv` instalado.

Passos:
1. Atualize a versão no `pyproject.toml` (sem reusar versão já publicada).
2. Gere os artefatos:
   - `uv build`
3. Publique (uma das opções):
   - Via uv (token): `uv publish --token "$PYPITOKEN"`
   - Via Twine (usa ~/.pypirc):
     - Ative o venv (opcional) e instale Twine:
       - `python -m ensurepip --upgrade && python -m pip install --upgrade twine`
     - Valide artefatos: `python -m twine check dist/*`
     - Publique: `python -m twine upload --repository pypi dist/*`

Dica: Publique no TestPyPI antes se preferir validar a página de projeto: `--repository testpypi`.

### Uso via uvx

- Instala e executa o CLI diretamente:
  - `uvx buscador-de-cnpj --help`
  - `uvx buscador-de-cnpj`

Se o comando iniciar o servidor imediatamente, `--help` pode não listar opções; nesse caso, consulte o README ou o código de `cli_main`.

## Execução Local (Desenvolvimento)

1. Crie/ative o ambiente:
   - `python3 -m venv .venv && source .venv/bin/bin/activate` (ou use `uv venv && source .venv/bin/activate`)
2. Instale dependências para dev (se necessário):
   - `uv pip install -e .`
3. Configure `.env` (opcional) com `CNPJ_API_KEY`.
4. Rode o servidor MCP:
   - `python -m cnpj_mcp_server` (se exposto) ou
   - `buscador-de-cnpj` (entry point do pacote)

Logs de debug imprimem:
- Presença/ausência da API key
- Primeiros 10 caracteres da chave
- CNPJ normalizado

## Boas Práticas de Desenvolvimento

### Estilo e Convenções
- Siga o código existente: tipagem, nomes, estrutura de pastas e padrões do MCP.
- Comentários explicam o “porquê”, não o “quê”. Evite comentários redundantes.
- Não exponha segredos em logs ou commits. Máscare a API key em logs (ex.: 10 primeiros chars).

### Dependências
- Não assuma bibliotecas; verifique `pyproject.toml` antes.
- Mantenha versões mínimas compatíveis e testes ao atualizar libs.

### Tratamento de Erros
- Diferencie erros de autenticação (401) de não encontrado (404).
- Propague mensagens de erro da API com contexto suficiente para diagnóstico.
- Valide entradas (ex.: CNPJ com 14 dígitos) antes de chamar a API.

### Testes
- Adicione testes unitários para funções utilitárias (ex.: limpeza/validação de CNPJ).
- Para integrações HTTP, use mocks ou um modo de sandbox quando possível.
- Se houver suite de testes no projeto, descubra como rodar (ex.: `pytest`) e mantenha-a verde.

### Versionamento e Releases
- Use SemVer: patch para correções e docs, minor para funcionalidades compatíveis, major para quebras.
- Nunca reutilize versões já publicadas em PyPI (erro 400 “File already exists”).
- Atualize o CHANGELOG/README com pontos relevantes.

### Segurança
- Headers: envie `x-api-key` exclusivamente por header.
- Evite registrar payloads sensíveis em logs.
- Revise PRs com foco em manuseio de segredos e endpoints.

### Observabilidade
- Logue eventos-chave (início do servidor, rota chamada, status HTTP).
- Limite logs verbosos em produção; torne-os configuráveis via env (ex.: `LOG_LEVEL`).

## Resolução de Problemas

- “File already exists” ao publicar: incremente `version` em `pyproject.toml` e gere artefatos novamente.
- “Missing credentials” ao publicar com `uv`: forneça `--token` ou configure `~/.pypirc` e use Twine.
- uvx não mostra help: o entry point pode iniciar o servidor direto; verifique README/código.
- 401 na API: verifique variáveis de ambiente e envio do header `x-api-key`.

## Referências
- PyPI: https://pypi.org/project/buscador-de-cnpj/
- OpenAPI (trechos relevantes): Autenticação por `x-api-key` (APIKeyHeader), rotas `/cnpj/{cnpj}`, `/search/`, `/search/csv`.
- MCP (Model Context Protocol): https://github.com/modelcontextprotocol/
