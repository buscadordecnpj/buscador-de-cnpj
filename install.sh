#!/bin/bash

# Script de instalação automática do Buscador de CNPJ
# Uso: curl -sSL https://raw.githubusercontent.com/victortavernari/buscador-de-cnpj/main/install.sh | bash

set -e

echo "🚀 Instalando Buscador de CNPJ..."

# Detectar o sistema operacional
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    CONFIG_DIR="$HOME/.config/claude"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
    CONFIG_DIR="$APPDATA/Claude"
else
    echo "❌ Sistema operacional não suportado: $OSTYPE"
    exit 1
fi

echo "✅ Sistema detectado: $PLATFORM"

# Verificar se uv está instalado
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando uv..."
    if [[ "$PLATFORM" == "windows" ]]; then
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    # Adicionar ao PATH da sessão atual
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✅ uv já está instalado"
fi

# Instalar o pacote via pip como fallback
echo "📦 Instalando buscador-de-cnpj..."
pip install --user buscador-de-cnpj

# Criar wrapper script
echo "🔧 Criando script wrapper..."
WRAPPER_DIR="/usr/local/bin"
if [[ "$PLATFORM" == "macos" || "$PLATFORM" == "linux" ]]; then
    sudo mkdir -p "$WRAPPER_DIR" || {
        echo "⚠️  Não foi possível criar wrapper em /usr/local/bin (sem sudo)"
        echo "📝 Use a Opção B (pip install) na documentação"
        WRAPPER_DIR="$HOME/.local/bin"
        mkdir -p "$WRAPPER_DIR"
    }
fi

# Encontrar uvx
UVX_PATH=""
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
    for expanded in $path; do
        if [[ -x "$expanded" ]]; then
            UVX_PATH="$expanded"
            break 2
        fi
    done
done

# Criar configuração para Claude Desktop
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
mkdir -p "$CONFIG_DIR"

echo "📝 Configurando Claude Desktop..."

# Criar configuração baseada no que está disponível
if [[ -n "$UVX_PATH" && -w "$WRAPPER_DIR" ]]; then
    # Opção A: uvx com wrapper
    cat > "$WRAPPER_DIR/uvx-wrapper" << EOF
#!/bin/bash
exec "$UVX_PATH" "\$@"
EOF
    chmod +x "$WRAPPER_DIR/uvx-wrapper"
    
    COMMAND="$WRAPPER_DIR/uvx-wrapper"
    ARGS='["buscador-de-cnpj"]'
    echo "✅ Configurado com uvx wrapper"
else
    # Opção B: pip install
    COMMAND="buscador-de-cnpj"
    ARGS='[]'
    echo "✅ Configurado com pip install"
fi

# Criar ou atualizar configuração
if [[ -f "$CONFIG_FILE" ]]; then
    echo "⚠️  Arquivo de configuração já existe. Backup criado."
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
fi

cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "cnpj-search": {
      "command": "$COMMAND",
      "args": $ARGS,
      "env": {
        "CNPJ_API_KEY": ""
      }
    }
  }
}
EOF

echo ""
echo "🎉 Instalação concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Obtenha uma API key em: https://buscadordecnpj.com"
echo "2. Edite o arquivo: $CONFIG_FILE"
echo "3. Adicione sua API key no campo CNPJ_API_KEY"
echo "4. Reinicie o Claude Desktop"
echo ""
echo "🔧 Para testar:"
echo "npx @modelcontextprotocol/inspector $COMMAND"
echo ""