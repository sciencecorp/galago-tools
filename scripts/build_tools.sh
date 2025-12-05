#!/usr/bin/env bash
#
# Build tool drivers for Electron Desktop App
#
# USAGE:
#   ./scripts/build_tools.sh                    # Build all tools
#   ./scripts/build_tools.sh pf400 opentrons2   # Build specific tools
#   ./scripts/build_tools.sh --clean            # Clean before build
#
# OPTIONS:
#   --clean     Clean build directories before building
#   --skip-venv Skip virtual environment creation (use current env)
#   --python    Path to Python executable (default: python3)
#

set -e

# Configuration
PYTHON=${PYTHON:-python3}
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/dist/tools"
CLEAN=false
SKIP_VENV=false
TOOLS=""

# All available tools (space-separated string for compatibility)
ALL_TOOLS="alps3000 bioshake bravo cytation dataman70 hamilton hig_centrifuge liconic microserve opentrons2 pf400 plateloc plr pyhamilton spectramax toolbox vcode vprep xpeel"

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --python)
            PYTHON="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [TOOLS...]"
            echo ""
            echo "Options:"
            echo "  --clean      Clean build directories before building"
            echo "  --skip-venv  Skip virtual environment creation"
            echo "  --python     Path to Python executable (default: python3)"
            echo "  --output     Output directory (default: dist/tools)"
            echo ""
            echo "Available tools: $ALL_TOOLS"
            exit 0
            ;;
        *)
            TOOLS="$TOOLS $1"
            shift
            ;;
    esac
done

# If no tools specified, build all
if [ -z "$TOOLS" ]; then
    TOOLS="$ALL_TOOLS"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}Galago Tools Builder for Electron Desktop${NC}"
echo -e "${CYAN}============================================${NC}"
echo "Python: $PYTHON"
echo "Tools to build:$TOOLS"
echo ""

# Verify Python exists
if ! command -v "$PYTHON" &> /dev/null; then
    echo -e "${RED}ERROR: Python not found at $PYTHON${NC}"
    exit 1
fi

# Generate gRPC interfaces first with correct protobuf version
echo -e "${YELLOW}Generating gRPC interfaces...${NC}"
cd "$PROJECT_ROOT"

# Install grpcio-tools with pinned protobuf to ensure version compatibility
$PYTHON -m pip install "grpcio-tools>=1.60.0,<2.0.0" "protobuf>=5.26.0,<6.0.0" --quiet 2>/dev/null || true

# Clear old generated files to avoid version conflicts
rm -f tools/grpc_interfaces/*.py tools/grpc_interfaces/*.pyi 2>/dev/null || true

# Generate proto files
PROTO_SRC="./interfaces"
GRPC_OUT="./tools/grpc_interfaces"
mkdir -p "$GRPC_OUT"

$PYTHON -m grpc_tools.protoc \
    -I${PROTO_SRC} \
    --python_out=${GRPC_OUT} \
    --pyi_out=${GRPC_OUT} \
    --grpc_python_out=${GRPC_OUT} \
    ${PROTO_SRC}/tools/grpc_interfaces/*.proto 2>/dev/null || {
    echo -e "${YELLOW}WARNING: Could not generate gRPC interfaces.${NC}"
}

# Move files if they were generated in nested directory
if [ -d "${GRPC_OUT}/tools/grpc_interfaces" ]; then
    mv ${GRPC_OUT}/tools/grpc_interfaces/*.py ${GRPC_OUT}/ 2>/dev/null || true
    mv ${GRPC_OUT}/tools/grpc_interfaces/*.pyi ${GRPC_OUT}/ 2>/dev/null || true
    rm -rf ${GRPC_OUT}/tools 2>/dev/null || true
fi

echo -e "${GREEN}gRPC interfaces generated${NC}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Track results
SUCCESS_TOOLS=""
FAILED_TOOLS=""
SKIPPED_TOOLS=""

for tool in $TOOLS; do
    tool_dir="$PROJECT_ROOT/tools/$tool"
    spec_file="$tool_dir/$tool.spec"
    
    if [ ! -f "$spec_file" ]; then
        echo -e "${YELLOW}SKIP: $tool - spec file not found${NC}"
        SKIPPED_TOOLS="$SKIPPED_TOOLS $tool"
        continue
    fi
    
    echo ""
    echo -e "${YELLOW}Building $tool...${NC}"
    echo "----------------------------------------"
    
    cd "$tool_dir"
    
    # Create virtual environment if not skipping
    if [ "$SKIP_VENV" = false ]; then
        venv_path="$tool_dir/venv"
        
        if [ "$CLEAN" = true ] && [ -d "$venv_path" ]; then
            echo "  Cleaning existing venv..."
            rm -rf "$venv_path"
        fi
        
        if [ ! -d "$venv_path" ]; then
            echo "  Creating virtual environment..."
            $PYTHON -m venv "$venv_path"
        fi
        
        # Activate venv
        source "$venv_path/bin/activate"
        
        # Install dependencies
        echo "  Installing dependencies..."
        pip install --quiet --upgrade pip
        # Pin protobuf to 5.x to avoid version mismatch with generated code
        pip install --quiet pyinstaller "grpcio>=1.60.0,<2.0.0" "grpcio-reflection>=1.60.0,<2.0.0" "protobuf>=5.26.0,<6.0.0" pydantic
        
        # Install tool-specific dependencies
        if [ -f "$tool_dir/requirements.txt" ]; then
            pip install --quiet -r "$tool_dir/requirements.txt" 2>/dev/null || true
        fi
        
        # Install common requirements
        if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
            pip install --quiet -r "$PROJECT_ROOT/requirements.txt" 2>/dev/null || true
        fi
    fi
    
    # Clean previous build
    if [ "$CLEAN" = true ]; then
        rm -rf "$tool_dir/build" "$tool_dir/dist"
    fi
    
    # Run PyInstaller
    echo "  Running PyInstaller..."
    build_success=true
    if ! pyinstaller "$spec_file" --clean --noconfirm 2>&1 | grep -E "error|Error" | grep -v "UPX" | head -5; then
        # Check if output exists despite grep output
        true
    fi
    
    # Check if build succeeded
    built_dir="$tool_dir/dist/$tool"
    if [ -d "$built_dir" ]; then
        dest_dir="$OUTPUT_DIR/$tool"
        rm -rf "$dest_dir"
        cp -r "$built_dir" "$dest_dir"
        echo -e "  ${GREEN}SUCCESS: Built to $dest_dir${NC}"
        SUCCESS_TOOLS="$SUCCESS_TOOLS $tool"
    else
        echo -e "  ${RED}FAILED: Build output not found${NC}"
        FAILED_TOOLS="$FAILED_TOOLS $tool"
    fi
    
    # Deactivate venv
    if [ "$SKIP_VENV" = false ]; then
        deactivate 2>/dev/null || true
    fi
done

# Summary
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}Build Summary${NC}"
echo -e "${CYAN}============================================${NC}"

# Count results
success_count=0
failed_count=0
skipped_count=0

for tool in $SUCCESS_TOOLS; do
    echo -e "  ${GREEN}$tool: SUCCESS${NC}"
    success_count=$((success_count + 1))
done

for tool in $FAILED_TOOLS; do
    echo -e "  ${RED}$tool: FAILED${NC}"
    failed_count=$((failed_count + 1))
done

for tool in $SKIPPED_TOOLS; do
    echo -e "  ${YELLOW}$tool: SKIPPED${NC}"
    skipped_count=$((skipped_count + 1))
done

echo ""
echo -e "${CYAN}Total: $success_count succeeded, $failed_count failed, $skipped_count skipped${NC}"
echo "Output directory: $OUTPUT_DIR"

if [ $failed_count -gt 0 ]; then
    exit 1
fi
