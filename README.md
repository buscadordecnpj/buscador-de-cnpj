# Buscador de CNPJ - MCP Server

Um servidor MCP (Model Context Protocol) para busca de dados de empresas brasileiras usando a API do [buscadordecnpj.com](https://buscadordecnpj.com).

![Demonstração do Buscador de CNPJ funcionando em um agente (GIF)](./example.gif)

## 📋 Funcionalidades

### 🆓 Consultas Gratuitas
- **cnpj_public_lookup**: Busca pública de dados básicos de uma empresa (sem necessidade de API key)

### 💎 Consultas Premium (requer API key)
- **cnpj_detailed_lookup**: Busca detalhada com dados completos da empresa
- **term_search**: Busca por termo textual (linguagem natural) em múltiplos campos; ex.: "padarias em SP Tatuapé"
- **cnpj_advanced_search**: Busca avançada com filtros estruturados (exatos, intervalos); ideal para fine-tuning

## 🚀 Instalação

### 🎯 Instalação Automática (Recomendada)
```bash
curl -sSL https://raw.githubusercontent.com/victortavernari/buscador-de-cnpj/main/install.sh | bash
```

Este script irá:
- ✅ Detectar seu sistema operacional
- ✅ Instalar uv (se necessário)
- ✅ Instalar buscador-de-cnpj
- ✅ Configurar automaticamente o Claude Desktop
- ✅ Criar wrapper scripts para compatibilidade

### 🔧 Instalação Manual

#### Opção A: Usando uv
```bash
# Instale uv (se não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh
# ou no Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Opção B: Usando pip
```bash
pip install buscador-de-cnpj
```

### 🔑 Configure sua API key
Para funcionalidades premium, obtenha uma API key em: https://buscadordecnpj.com

## 🔧 Configuração no Claude Desktop

### 1. Edite o arquivo de configuração do Claude
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 2. Adicione a configuração do MCP server

#### Opção A: Usando uvx com script wrapper (recomendado)

**1. Crie um script wrapper:**
```bash
# Crie o diretório se não existir
sudo mkdir -p /usr/local/bin

# Crie o script wrapper
sudo tee /usr/local/bin/uvx-wrapper << 'EOF'
#!/bin/bash
# Encontra uvx automaticamente e executa
UVX_PATH=""

# Possíveis localizações do uvx
POSSIBLE_PATHS=(
    "$HOME/.local/bin/uvx"
    "$HOME/Library/Python/3.*/bin/uvx"
    "/opt/homebrew/bin/uvx"
    "/usr/local/bin/uvx"
    "$(which uvx 2>/dev/null)"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if [[ -x "$path" ]]; then
        UVX_PATH="$path"
        break
    fi
    # Para paths com wildcard
    for expanded in $path; do
        if [[ -x "$expanded" ]]; then
            UVX_PATH="$expanded"
            break 2
        fi
    done
done

if [[ -z "$UVX_PATH" ]]; then
    echo "Error: uvx not found. Please install uv first." >&2
    exit 1
fi

exec "$UVX_PATH" "$@"
EOF

# Torne executável
sudo chmod +x /usr/local/bin/uvx-wrapper
```

**2. Configure no Claude Desktop:**
```json
{
  "mcpServers": {
    "cnpj-search": {
      "command": "/usr/local/bin/uvx-wrapper",
      "args": ["buscador-de-cnpj"],
      "env": {
        "CNPJ_API_KEY": "sua_api_key_aqui"
      }
    }
  }
}
```

#### Opção B: Instalação global com pip (mais simples)
```bash
pip install buscador-de-cnpj
```

```json
{
  "mcpServers": {
    "cnpj-search": {
      "command": "buscador-de-cnpj",
      "env": {
        "CNPJ_API_KEY": "sua_api_key_aqui"
      }
    }
  }
}
```

#### Opção C: Caminho manual (se outras não funcionarem)
**1. Encontre seu caminho do uvx:**
```bash
which uvx
```

**2. Use o caminho completo:**
```json
{
  "mcpServers": {
    "cnpj-search": {
      "command": "/seu/caminho/para/uvx",
      "args": ["buscador-de-cnpj"],
      "env": {
        "CNPJ_API_KEY": "sua_api_key_aqui"
      }
    }
  }
}
```

### 3. Reinicie o Claude Desktop
Feche e abra novamente o Claude Desktop para carregar o novo servidor MCP.

## 📖 Como Usar

Para detalhes de deploy, validação e melhores práticas, consulte também o QWEN.md.

### Consulta Pública (Gratuita)
```
Busque informações da empresa com CNPJ 11.222.333/0001-81
```

### Busca Detalhada (Premium)
```
Faça uma busca detalhada da empresa com CNPJ 11.222.333/0001-81
```

### Busca em Lote
```
Busque informações das empresas com CNPJs: 11.222.333/0001-81, 22.333.444/0001-92
```

### Busca Avançada
```
Busque empresas com nome "Petrobras" no estado do Rio de Janeiro que estejam ativas
```

## 🛠️ Exemplos de Uso Direto

### 1. Consulta Pública
```json
{
  "tool": "cnpj_public_lookup",
  "arguments": {
    "cnpj": "11.222.333/0001-81"
  }
}
```

### 2. Busca Detalhada
```json
{
  "tool": "cnpj_detailed_lookup",
  "arguments": {
    "cnpj": "11222333000181"
  }
}
```

### 3. Busca em Lote
```json
{
  "tool": "cnpj_bulk_lookup",
  "arguments": {
    "cnpjs": ["11222333000181", "22333444000192"],
    "state": "SP",
    "active": true
  }
}
```

### 4. Busca por Termo (Texto Livre)
```json
{
  "tool": "term_search",
  "arguments": {
    "term": "padarias em SP Tatuapé",
    "uf": "SP",
    "pagina": 1,
    "limite": 100
  }
}
```

Dica: use `term` para linguagem natural; combine com `uf`, `municipio`, `bairro` para acelerar e refinar.

### 5. Busca Avançada (Filtros Estruturados)
```json
{
  "tool": "cnpj_advanced_search",
  "arguments": {
    "razao_social": "*padaria*",
    "uf": "SP",
    "municipio": "São Paulo",
    "bairro": "Tatuapé",
    "situacao_cadastral": "2",
    "pagina": 1,
    "limite": 100
  }
}
```

## 🔍 Parâmetros Disponíveis

### cnpj_public_lookup
- **cnpj** (obrigatório): CNPJ da empresa (com ou sem formatação)

### cnpj_detailed_lookup
- **cnpj** (obrigatório): CNPJ da empresa (com ou sem formatação)

### cnpj_bulk_lookup
- **cnpjs** (obrigatório): Lista de CNPJs
- **state** (opcional): Filtrar por estado (UF)
- **active** (opcional): Filtrar apenas empresas ativas (true/false)

### cnpj_advanced_search
- **name** (opcional): Nome da empresa ou parte do nome
- **activity** (opcional): Atividade principal da empresa
- **state** (opcional): Estado (UF)
- **city** (opcional): Cidade
- **registration_status** (opcional): Status do registro (ATIVA, BAIXADA, etc.)
- **page** (opcional): Página dos resultados (padrão: 1)
- **per_page** (opcional): Resultados por página (máximo: 50)

## 💰 Custos da API

- **Consulta Pública**: Gratuita e ilimitada
- **Consulta Detalhada**: 1 crédito por consulta bem-sucedida
- **Busca em Lote**: 1 crédito por 20 CNPJs
- **Busca Avançada**: 2 créditos por busca

## 🚨 Solução de Problemas

### Erro: "spawn uvx ENOENT"
O Claude Desktop não encontra o `uvx`. Soluções:

**1. Encontre o caminho do uvx:**
```bash
which uvx
```

**2. Use o caminho completo na configuração:**
```json
{
  "command": "/caminho/completo/para/uvx",
  "args": ["buscador-de-cnpj"]
}
```

**3. Se o uvx não estiver instalado:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**4. Ou use a Opção B com pip install**

### Erro: "spawn buscador-de-cnpj ENOENT"
O pacote não está instalado globalmente. Execute:
```bash
pip install buscador-de-cnpj
```

### Erro: "API key required"
Para funcionalidades premium:
1. Defina a variável de ambiente: `export CNPJ_API_KEY="sua_key"`
2. Ou configure no arquivo de configuração do Claude Desktop
3. Obtenha uma API key em: https://buscadordecnpj.com

### Erro: "Unknown tool"
Verifique se:
1. O Claude Desktop foi reiniciado após a configuração
2. A configuração JSON está correta (sem erros de sintaxe)
3. O nome do servidor está correto: "cnpj-search"

### Servidor não conecta
Confirme que:
1. Python 3.11+ está instalado
2. O pacote foi instalado corretamente
3. Não há conflitos de dependências

## 🔍 Debugging

Para testar o servidor MCP localmente, use o MCP Inspector:

### Com uvx
```bash
npx @modelcontextprotocol/inspector uvx buscador-de-cnpj
```

### Com pip install
```bash
npx @modelcontextprotocol/inspector buscador-de-cnpj
```

Isso abrirá uma interface web onde você pode testar as ferramentas do MCP server diretamente.

## 📞 Suporte

- **API**: https://buscadordecnpj.com
- **Documentação da API**: https://api.buscadordecnpj.com/docs
- **MCP Protocol**: https://modelcontextprotocol.io

## 📄 Licença

Este projeto está licenciado sob a MIT License.
