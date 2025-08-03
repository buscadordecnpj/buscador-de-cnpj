import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Debug: verificar variáveis de ambiente
print(f"🔍 Debug - Variáveis de ambiente carregadas:")
print(f"🔍 CNPJ_API_KEY: {'✅ Presente' if os.getenv('CNPJ_API_KEY') else '❌ Ausente'}")
if os.getenv('CNPJ_API_KEY'):
    print(f"🔍 CNPJ_API_KEY valor: {os.getenv('CNPJ_API_KEY')[:10]}...")

# Server instance
server = Server("buscador-de-cnpj")

# Tool definitions
TOOLS = {
    "cnpj_detailed_lookup": {
        "name": "cnpj_detailed_lookup", 
        "description": "Busca detalhada de dados completos de uma empresa por CNPJ (requer API key)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cnpj": {
                    "type": "string",
                    "description": "CNPJ da empresa (somente números ou com formatação)"
                }
            },
            "required": ["cnpj"]
        }
    },
    "term_search": {
        "name": "term_search",
        "description": "Busca por termo em múltiplos campos (texto livre). Ideal para consultas genéricas como 'padarias em SP Tatuapé'. Requer API key; 2 créditos por requisição.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "Termo de busca textual. Aceita curingas como *padaria*"},
                "uf": {"type": "string", "description": "UF opcional (ex: SP). Acelera e refina os resultados."},
                "situacao_cadastral": {"type": "string", "description": "Situação opcional (ex: 2 para ATIVA)"},
                "faixa_faturamento_estimado": {"type": "string", "description": "Faixa de faturamento (ex: 0_360k, 360k_1kk, 1kk_4.8kk, 4.8kk_20kk, 20kk_mais)"},
                "pagina": {"type": "integer", "description": "Página (default 1)"},
                "limite": {"type": "integer", "description": "Limite por página (default/max 10000)"},
                "ordenarPor": {"type": "string", "description": "Campo de ordenação"},
                "ordenacaoDesc": {"type": "boolean", "description": "true para ordem descendente"}
            },
            "required": ["term"]
        }
    },
    "cnpj_advanced_search": {
        "name": "cnpj_advanced_search",
        "description": "Busca avançada com filtros estruturados (exatos e intervalos). Use para refinamentos finos. Requer API key; 2 créditos por requisição.",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "razao_social": {"type": "string", "description": "Busca textual com curingas, ex: *padaria*"},
                "nome_fantasia": {"type": "string", "description": "Busca textual com curingas"},
                "cnae_principal": {"type": "string", "description": "Código CNAE principal (exato)"},
                "uf": {"type": "string", "description": "Estado (UF)"},
                "municipio": {"type": "string", "description": "Município (texto)"},
                "bairro": {"type": "string", "description": "Bairro (texto)"},
                "cep": {"type": "string", "description": "CEP (8 dígitos)"},
                "ddd": {"type": "string", "description": "DDD do telefone"},
                "situacao_cadastral": {"type": "string", "description": "Código (1,2,3,4,8)"},
                "porte_empresa": {"type": "string", "description": "Código do porte"},
                "capital_social_min": {"type": "number", "description": "Capital mínimo"},
                "capital_social_max": {"type": "number", "description": "Capital máximo"},
                "data_abertura_inicio": {"type": "string", "description": "YYYY-MM-DD"},
                "data_abertura_fim": {"type": "string", "description": "YYYY-MM-DD"},
                "pagina": {"type": "integer", "description": "Página (default 1)"},
                "limite": {"type": "integer", "description": "Limite por página (default/max 10000)"},
                "ordenarPor": {"type": "string", "description": "Campo de ordenação"},
                "ordenacaoDesc": {"type": "boolean", "description": "true para ordem descendente"}
            }
        }
    },
    "search_csv": {
        "name": "search_csv",
        "description": "Exporta resultados de busca em formato CSV (requer API key) - 2 créditos por página",
        "inputSchema": {
            "type": "object",
            "properties": {
                "razao_social": {"type": "string"},
                "nome_fantasia": {"type": "string"},
                "cnae_principal": {"type": "string"},
                "uf": {"type": "string"},
                "municipio": {"type": "string"},
                "bairro": {"type": "string"},
                "cep": {"type": "string"},
                "ddd": {"type": "string"},
                "situacao_cadastral": {"type": "string"},
                "porte_empresa": {"type": "string"},
                "capital_social_min": {"type": "number"},
                "capital_social_max": {"type": "number"},
                "data_abertura_inicio": {"type": "string"},
                "data_abertura_fim": {"type": "string"},
                "page": {"type": "integer", "description": "Página (primeira página gratuita)"}
            }
        }
    }
}


class CNPJClient:
    """Cliente para a API do Buscador de CNPJ.

    Este cliente foi pensado para ser usado por agentes LLM e aplicações automáticas,
    padronizando autenticação, validação de entradas e tratamento de respostas.

    Autenticação
    - Header: x-api-key: <sua_chave>
    - Origem: lida automaticamente de variáveis de ambiente (preferência nesta ordem):
      CNPJ_API_KEY, CNPJ_API_TOKEN, BUSCADOR_CNPJ_API_KEY, API_KEY
    - Segurança: a chave NUNCA é enviada por query string, apenas via header.

    Variáveis de Ambiente Suportadas
    - CNPJ_API_KEY: principal recomendada
    - CNPJ_API_TOKEN: alternativa aceita
    - BUSCADOR_CNPJ_API_KEY: alternativa aceita
    - API_KEY: alternativa genérica

    Exemplos de uso (equivalentes HTTP diretos)
    - Consulta por CNPJ (detalhada):
      curl -H "x-api-key: YOUR_API_KEY" "http://localhost:8001/cnpj/47271733000124"

    - Busca avançada (Manticore Search):
      curl -H "x-api-key: YOUR_API_KEY" "http://localhost:8001/search/?term=empresa"

    Observações para agentes LLM
    - Sempre envie o header x-api-key.
    - Não inclua a chave em params.
    - Garanta CNPJ com 14 dígitos numéricos (use _clean_cnpj antes de consultar).
    - Trate 401 como falta/erro de chave e 404 como CNPJ não encontrado.
    """
    
    def __init__(self):
        self.base_url = "https://api.buscadordecnpj.com"
        
        # Tentar múltiplas formas de obter a API key
        self.api_key = (
            os.getenv("CNPJ_API_KEY") or 
            os.getenv("CNPJ_API_TOKEN") or
            os.getenv("BUSCADOR_CNPJ_API_KEY") or
            os.getenv("API_KEY")
        )
        
        # Debug: verificar se a API key foi carregada
        print(f"🔍 Debug - Todas as variáveis de ambiente:")
        for key, value in os.environ.items():
            if 'api' in key.lower() or 'cnpj' in key.lower() or 'key' in key.lower():
                print(f"🔍 {key}: {value[:10]}..." if value else f"🔍 {key}: (vazio)")
        
        if self.api_key:
            print(f"✅ API key carregada: {self.api_key[:10]}...")
        else:
            print("⚠️ API key não encontrada! Verifique as variáveis de ambiente.")
        
        # Headers padrão com API key quando disponível
        self.default_headers: Dict[str, str] = {}
        if self.api_key:
            self.default_headers["x-api-key"] = self.api_key
        
    def _clean_cnpj(self, cnpj: str) -> str:
        """Remove caracteres não numéricos e valida que o CNPJ tenha 14 dígitos."""
        cleaned = ''.join(filter(str.isdigit, cnpj))
        print(f"🔍 Debug - CNPJ original: {cnpj}")
        print(f"🔍 Debug - CNPJ limpo: {cleaned}")
        
        if len(cleaned) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos. Recebido: {len(cleaned)} dígitos ({cleaned})")
        
        return cleaned
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição GET para a API.

        Parâmetros
        - endpoint: caminho do recurso (ex: "/cnpj/00000000000000", "/search/")
        - params: dicionário de query string (NÃO incluir credenciais)
        - headers: headers adicionais (serão mesclados; x-api-key já é definido por padrão)
        """
        url = f"{self.base_url}{endpoint}"
        
        merged_headers = {**self.default_headers, **(headers or {})}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=merged_headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def _make_post_request(self, endpoint: str, data: Optional[Dict] = None, 
                               headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição POST para a API.

        Parâmetros
        - endpoint: caminho do recurso (ex: "/cnpj/list")
        - data: corpo JSON a ser enviado
        - headers: headers adicionais (serão mesclados; x-api-key já é definido por padrão)
        """
        url = f"{self.base_url}{endpoint}"
        
        merged_headers = {**self.default_headers, **(headers or {})}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=merged_headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def detailed_lookup(self, cnpj: str) -> Dict[str, Any]:
        """Consulta detalhada de CNPJ (consumo de créditos conforme a API).

        - cnpj: string que pode conter máscara; será normalizada para 14 dígitos.
        - Autenticação: via header x-api-key (já configurado)
        - Erros comuns: 401 (chave ausente/ inválida), 404 (CNPJ não encontrado)
        """
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para busca detalhada!\n\n"
                "Para usar esta funcionalidade premium:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop\n"
                "3. Ou use a busca pública gratuita com 'cnpj_public_lookup'\n\n"
                "💡 A busca pública oferece dados básicos sem necessidade de API key."
            )
        
        clean_cnpj = self._clean_cnpj(cnpj)
        endpoint = f"/cnpj/{clean_cnpj}"
        return await self._make_request(endpoint)
    
    async def advanced_search(self, **kwargs) -> Dict[str, Any]:
        """Busca avançada parametrizada (consome créditos por requisição).

        Use quando precisar de filtros estruturados (exatos/intervalos). Para
        consultas de linguagem natural (e.g., "padarias em SP Tatuapé"), prefira
        `term_search` que agrega campos textuais automaticamente.

        Exemplos de filtros aceitos (não exaustivo):
        - uf, municipio, bairro, cep
        - razao_social, nome_fantasia (textuais com curingas)
        - cnae_principal (código), descricao_cnae_fiscal_principal (texto)
        - situacao_cadastral, porte_empresa
        - capital_social_min, capital_social_max
        - data_abertura_inicio, data_abertura_fim (YYYY-MM-DD)

        Observações
        - Não incluir a API key em params; ela é enviada no header automaticamente.
        - Todos os filtros são combinados com AND na API.
        """
        print(f"🔍 Debug - API key disponível: {bool(self.api_key)}")
        if self.api_key:
            print(f"🔍 Debug - API key: {self.api_key[:10]}...")
        
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para busca avançada!\n\n"
                "Esta é uma funcionalidade premium que permite buscar por:\n"
                "• Nome da empresa, atividade, localização\n"
                "• Filtros avançados por status, porte, etc.\n\n"
                "Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop\n\n"
                "💡 Alternativa gratuita: Use 'cnpj_public_lookup' se você tiver o CNPJ específico."
            )
        
        endpoint = "/search/"
        params = {k: v for k, v in kwargs.items() if v is not None}
        print(f"🔍 Debug - Parâmetros: {params}")
        
        return await self._make_request(endpoint, params=params)
    
    async def search_csv(self, **kwargs) -> Dict[str, Any]:
        """Exporta resultados de busca para CSV (2 créditos por página; 1ª grátis).

        Parâmetros de paginação e ordenação aceitos pela API:
        - pagina_inicio: inteiro (default 1)
        - pagina_fim: inteiro (default 1)
        - limite: inteiro (default/max 10000)
        - ordenarPor: string
        - ordenacaoDesc: booleano

        Observações
        - Reaproveita os mesmos filtros de /search.
        - Não inclua a API key em params; ela é enviada no header automaticamente.
        """
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para exportação CSV!\n\n"
                "Esta é uma funcionalidade premium. Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop\n\n"
                "💡 Primeira página é gratuita, páginas subsequentes custam 2 créditos cada."
            )
        
        endpoint = "/search/csv"
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        return await self._make_request(endpoint, params=params)
    
# Initialize client
cnpj_client = CNPJClient()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista as ferramentas disponíveis"""
    return [
        Tool(
            name=tool_info["name"],
            description=tool_info["description"], 
            inputSchema=tool_info["inputSchema"]
        )
        for tool_info in TOOLS.values()
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Executa uma ferramenta"""
    
    try:
        if name == "cnpj_detailed_lookup":
            result = await cnpj_client.detailed_lookup(arguments["cnpj"])
    
        elif name == "term_search":
            result = await cnpj_client.advanced_search(**arguments)

        elif name == "cnpj_advanced_search":
            result = await cnpj_client.advanced_search(**arguments)
            
        elif name == "search_csv":
            result = await cnpj_client.search_csv(**arguments)
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text", 
            text=f"Error: {str(e)}"
        )]


async def main():
    """Função principal para executar o servidor"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli_main():
    """Entry point para o CLI"""
    import asyncio
    asyncio.run(main())