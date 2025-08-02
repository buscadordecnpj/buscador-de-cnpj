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

# Server instance
server = Server("cnpj-mcp-server")

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
                    "description": "Lista de CNPJs para buscar"
                },
                "state": {
                    "type": "string",
                    "description": "Filtrar por estado (opcional)"
                },
                "active": {
                    "type": "boolean",
                    "description": "Filtrar apenas empresas ativas (opcional)"
                }
            },
            "required": ["cnpjs"]
        }
    },
    "cnpj_advanced_search": {
        "name": "cnpj_advanced_search",
        "description": "Busca avançada com filtros personalizados (requer API key)",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nome da empresa ou parte do nome"
                },
                "activity": {
                    "type": "string",
                    "description": "Atividade principal da empresa"
                },
                "state": {
                    "type": "string",
                    "description": "Estado (UF)"
                },
                "city": {
                    "type": "string", 
                    "description": "Cidade"
                },
                "registration_status": {
                    "type": "string",
                    "description": "Status do registro (ATIVA, BAIXADA, etc.)"
                },
                "page": {
                    "type": "integer",
                    "description": "Página dos resultados (padrão: 1)"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Resultados por página (máximo: 50)"
                }
            }
        }
    }
}


class CNPJClient:
    """Cliente para a API do buscador de CNPJ"""
    
    def __init__(self):
        self.base_url = "https://api.buscadordecnpj.com"
        self.api_key = os.getenv("CNPJ_API_KEY")
        
    def _clean_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ"""
        return ''.join(filter(str.isdigit, cnpj))
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição HTTP para a API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
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
            raise Exception("API key required for detailed lookup. Set CNPJ_API_KEY environment variable.")
        
        clean_cnpj = self._clean_cnpj(cnpj)
        endpoint = f"/cnpj/{clean_cnpj}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, headers=headers)
    
    async def bulk_lookup(self, cnpjs: List[str], state: Optional[str] = None, 
                         active: Optional[bool] = None) -> Dict[str, Any]:
        """Busca em lote de CNPJs"""
        if not self.api_key:
            raise Exception("API key required for bulk lookup. Set CNPJ_API_KEY environment variable.")
        
        clean_cnpjs = [self._clean_cnpj(cnpj) for cnpj in cnpjs]
        endpoint = "/cnpj/list"
        
        params = {"cnpjs": ",".join(clean_cnpjs)}
        if state:
            params["state"] = state
        if active is not None:
            params["active"] = str(active).lower()
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._make_request(endpoint, params=params, headers=headers)
    
    async def advanced_search(self, **kwargs) -> Dict[str, Any]:
        """Busca avançada com filtros"""
        if not self.api_key:
            raise Exception("API key required for advanced search. Set CNPJ_API_KEY environment variable.")
        
        endpoint = "/search/"
        
        # Remove parâmetros vazios
        params = {k: v for k, v in kwargs.items() if v is not None}
        
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
                arguments.get("state"),
                arguments.get("active")
            )
            
        elif name == "cnpj_advanced_search":
            result = await cnpj_client.advanced_search(**arguments)
            
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