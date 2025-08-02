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
    "cnpj_public_lookup": {
        "name": "cnpj_public_lookup",
        "description": "Busca pública gratuita de dados básicos de uma empresa por CNPJ",
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
    "cnpj_bulk_lookup": {
        "name": "cnpj_bulk_lookup",
        "description": "Busca em lote de múltiplos CNPJs (requer API key)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cnpjs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de CNPJs para buscar (até 20 por requisição)"
                },
                "uf": {
                    "type": "string",
                    "description": "Filtrar por estado (UF) - opcional"
                },
                "situacao_cadastral": {
                    "type": "string",
                    "description": "Filtrar por situação cadastral - opcional"
                }
            },
            "required": ["cnpjs"]
        }
    },
    "cnpj_advanced_search": {
        "name": "cnpj_advanced_search",
        "description": "Busca avançada com filtros personalizados (requer API key) - 2 créditos",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "razao_social": {
                    "type": "string",
                    "description": "Razão social da empresa"
                },
                "nome_fantasia": {
                    "type": "string",
                    "description": "Nome fantasia da empresa"
                },
                "cnae_principal": {
                    "type": "string",
                    "description": "CNAE principal da atividade"
                },
                "uf": {
                    "type": "string",
                    "description": "Estado (UF)"
                },
                "municipio": {
                    "type": "string", 
                    "description": "Município"
                },
                "bairro": {
                    "type": "string", 
                    "description": "Bairro"
                },
                "cep": {
                    "type": "string", 
                    "description": "CEP"
                },
                "ddd": {
                    "type": "string", 
                    "description": "DDD do telefone"
                },
                "situacao_cadastral": {
                    "type": "string",
                    "description": "Situação cadastral (ATIVA, BAIXADA, etc.)"
                },
                "porte_empresa": {
                    "type": "string",
                    "description": "Porte da empresa (PEQUENO, MEDIO, GRANDE, etc.)"
                },
                "capital_social_min": {
                    "type": "number",
                    "description": "Capital social mínimo"
                },
                "capital_social_max": {
                    "type": "number",
                    "description": "Capital social máximo"
                },
                "data_abertura_inicio": {
                    "type": "string",
                    "description": "Data de abertura inicial (YYYY-MM-DD)"
                },
                "data_abertura_fim": {
                    "type": "string",
                    "description": "Data de abertura final (YYYY-MM-DD)"
                },
                "page": {
                    "type": "integer",
                    "description": "Página dos resultados (padrão: 1)"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Resultados por página (máximo: 50, padrão: 10)"
                }
            }
        }
    },
    "search_estimate": {
        "name": "search_estimate",
        "description": "Estima o custo em créditos de uma busca avançada (gratuito)",
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
                "data_abertura_fim": {"type": "string"}
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
                "page": {"type": "integer", "description": "Página (primeira página gratuita)"},
                "per_page": {"type": "integer", "description": "Registros por página (máx: 1000)"}
            }
        }
    },
    "csv_estimate": {
        "name": "csv_estimate", 
        "description": "Estima o custo em créditos de exportação CSV (gratuito)",
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
                "per_page": {"type": "integer", "description": "Registros por página (máx: 1000)"}
            }
        }
    },
    "logs_summary": {
        "name": "logs_summary",
        "description": "Resumo dos logs de uso da API (requer API key)",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    "logs_history": {
        "name": "logs_history", 
        "description": "Histórico detalhado de logs da API (requer API key)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Página dos resultados"},
                "per_page": {"type": "integer", "description": "Registros por página"}
            }
        }
    }
}


class CNPJClient:
    """Cliente para a API do buscador de CNPJ"""
    
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
        
    def _clean_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ"""
        cleaned = ''.join(filter(str.isdigit, cnpj))
        print(f"🔍 Debug - CNPJ original: {cnpj}")
        print(f"🔍 Debug - CNPJ limpo: {cleaned}")
        
        # Validar se tem 14 dígitos
        if len(cleaned) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos. Recebido: {len(cleaned)} dígitos ({cleaned})")
        
        return cleaned
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição GET para a API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def _make_post_request(self, endpoint: str, data: Optional[Dict] = None, 
                               headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição POST para a API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def public_lookup(self, cnpj: str) -> Dict[str, Any]:
        """Busca pública gratuita de CNPJ"""
        clean_cnpj = self._clean_cnpj(cnpj)
        endpoint = f"/cnpj/public/{clean_cnpj}"
        return await self._make_request(endpoint)
    
    async def detailed_lookup(self, cnpj: str) -> Dict[str, Any]:
        """Busca detalhada com API key"""
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
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, headers=headers)
    
    async def bulk_lookup(self, cnpjs: List[str], uf: Optional[str] = None, 
                         situacao_cadastral: Optional[str] = None) -> Dict[str, Any]:
        """Busca em lote de CNPJs"""
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para busca em lote!\n\n"
                "Esta é uma funcionalidade premium. Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop\n\n"
                "💡 Alternativa: Use 'cnpj_public_lookup' para consultas individuais gratuitas."
            )
        
        clean_cnpjs = [self._clean_cnpj(cnpj) for cnpj in cnpjs]
        endpoint = "/cnpj/list"
        
        # Preparar dados para POST
        data = {"cnpjs": clean_cnpjs}
        if uf:
            data["uf"] = uf
        if situacao_cadastral:
            data["situacao_cadastral"] = situacao_cadastral
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_post_request(endpoint, data=data, headers=headers)
    
    async def advanced_search(self, **kwargs) -> Dict[str, Any]:
        """Busca avançada com filtros"""
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
        
        # Remove parâmetros vazios
        params = {k: v for k, v in kwargs.items() if v is not None}
        print(f"🔍 Debug - Parâmetros: {params}")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        print(f"🔍 Debug - Headers: Authorization Bearer {self.api_key[:10]}...")
        
        return await self._make_request(endpoint, params=params, headers=headers)
    
    async def search_estimate(self, **kwargs) -> Dict[str, Any]:
        """Estima o custo de uma busca avançada (gratuito)"""
        endpoint = "/search/estimate"
        
        # Remove parâmetros vazios
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        return await self._make_request(endpoint, params=params, headers=headers)
    
    async def search_csv(self, **kwargs) -> Dict[str, Any]:
        """Exporta resultados de busca em CSV"""
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para exportação CSV!\n\n"
                "Esta é uma funcionalidade premium. Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop\n\n"
                "💡 Primeira página é gratuita, páginas subsequentes custam 2 créditos cada."
            )
        
        endpoint = "/search/csv"
        
        # Remove parâmetros vazios
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, params=params, headers=headers)
    
    async def csv_estimate(self, **kwargs) -> Dict[str, Any]:
        """Estima o custo de exportação CSV (gratuito)"""
        endpoint = "/search/csv/estimate"
        
        # Remove parâmetros vazios
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        return await self._make_request(endpoint, params=params, headers=headers)
    
    async def logs_summary(self) -> Dict[str, Any]:
        """Resumo dos logs de uso da API"""
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para acessar logs!\n\n"
                "Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop"
            )
        
        endpoint = "/logs/summary"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, headers=headers)
    
    async def logs_history(self, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
        """Histórico detalhado de logs da API"""
        if not self.api_key:
            raise Exception(
                "🔑 API key necessária para acessar histórico de logs!\n\n"
                "Para usar:\n"
                "1. Obtenha sua API key em: https://buscadordecnpj.com\n"
                "2. Configure a variável CNPJ_API_KEY no Claude Desktop"
            )
        
        endpoint = "/logs/history"
        
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, params=params, headers=headers)


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
        if name == "cnpj_public_lookup":
            result = await cnpj_client.public_lookup(arguments["cnpj"])
            
        elif name == "cnpj_detailed_lookup":
            result = await cnpj_client.detailed_lookup(arguments["cnpj"])
            
        elif name == "cnpj_bulk_lookup":
            result = await cnpj_client.bulk_lookup(
                arguments["cnpjs"],
                arguments.get("uf"),
                arguments.get("situacao_cadastral")
            )
            
        elif name == "cnpj_advanced_search":
            result = await cnpj_client.advanced_search(**arguments)
            
        elif name == "search_estimate":
            result = await cnpj_client.search_estimate(**arguments)
            
        elif name == "search_csv":
            result = await cnpj_client.search_csv(**arguments)
            
        elif name == "csv_estimate":
            result = await cnpj_client.csv_estimate(**arguments)
            
        elif name == "logs_summary":
            result = await cnpj_client.logs_summary()
            
        elif name == "logs_history":
            result = await cnpj_client.logs_history(
                arguments.get("page"),
                arguments.get("per_page")
            )
            
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