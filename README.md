# CNPJ MCP Server

Um servidor MCP (Model Context Protocol) para busca de dados de empresas brasileiras usando a API do [buscadordecnpj.com](https://buscadordecnpj.com).

## 📋 Funcionalidades

### 🆓 Consultas Gratuitas
- **cnpj_public_lookup**: Busca pública de dados básicos de uma empresa (sem necessidade de API key)

### 💎 Consultas Premium (requer API key)
- **cnpj_detailed_lookup**: Busca detalhada com dados completos da empresa
- **cnpj_bulk_lookup**: Busca em lote de múltiplos CNPJs (até 20 por requisição)
- **cnpj_advanced_search**: Busca avançada com filtros personalizados

## 🚀 Instalação

### Pré-requisitos
- Python 3.11 ou superior
- pip

### 1. Instale o pacote
```bash
pip install cnpj-mcp-server
```

### 2. Configure a API key (opcional para funcionalidades premium)
```bash
# Crie um arquivo .env no diretório do seu projeto
echo "CNPJ_API_KEY=sua_api_key_aqui" > .env
```

Para obter uma API key, visite: https://buscadordecnpj.com

## 🔧 Configuração no Claude Desktop

### 1. Edite o arquivo de configuração do Claude
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 2. Adicione a configuração do MCP server
```json
{
  "mcpServers": {
    "cnpj-search": {
      "command": "cnpj-mcp-server",
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

### 4. Busca Avançada
```json
{
  "tool": "cnpj_advanced_search",
  "arguments": {
    "name": "Petrobras",
    "state": "RJ",
    "registration_status": "ATIVA",
    "page": 1,
    "per_page": 10
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

### Erro: "API key required"
Certifique-se de que:
1. O arquivo `.env` existe na raiz do projeto
2. A variável `CNPJ_API_KEY` está definida corretamente
3. A API key é válida e tem créditos disponíveis

### Erro: "Unknown tool"
Verifique se:
1. O servidor MCP está rodando corretamente
2. O Claude Desktop foi reiniciado após a configuração
3. O nome da ferramenta está correto

### Servidor não inicia
Confirme que:
1. Python 3.11+ está instalado
2. As dependências foram instaladas com `pip install -e .`
3. Não há conflitos de porta

## 📞 Suporte

- **API**: https://buscadordecnpj.com
- **Documentação da API**: https://api.buscadordecnpj.com/docs
- **MCP Protocol**: https://modelcontextprotocol.io

## 📄 Licença

Este projeto está licenciado sob a MIT License.
