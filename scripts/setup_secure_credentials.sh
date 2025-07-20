#!/bin/bash
# TraderTerminal Secure Credential Setup
# Cross-platform installation and configuration script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Platform detection
PLATFORM=$(uname -s)
ARCH=$(uname -m)

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  TraderTerminal Secure Credential Setup"
    echo "=================================================="
    echo -e "${NC}"
    echo "Platform: $PLATFORM ($ARCH)"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_info "Checking system dependencies..."
    
    # Check Python 3.11+
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        print_error "Python 3.11+ is required (found: $PYTHON_VERSION)"
        exit 1
    fi
    print_status "Python $PYTHON_VERSION"
    
    # Check platform-specific requirements
    if [ "$PLATFORM" = "Darwin" ]; then
        # macOS - check for Command Line Tools
        if ! xcode-select -p &> /dev/null; then
            print_warning "Xcode Command Line Tools not found. Installing..."
            xcode-select --install
            echo "Please run this script again after installing Command Line Tools"
            exit 1
        fi
        print_status "macOS Command Line Tools"
        
    elif [ "$PLATFORM" = "Linux" ]; then
        # Linux - check for required packages
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            MISSING_PACKAGES=""
            for pkg in python3-dev libssl-dev libffi-dev libdbus-1-dev pkg-config; do
                if ! dpkg -l | grep -q "^ii  $pkg "; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done
            
            if [ -n "$MISSING_PACKAGES" ]; then
                print_warning "Installing required system packages:$MISSING_PACKAGES"
                sudo apt-get update
                sudo apt-get install -y $MISSING_PACKAGES
            fi
            print_status "Linux system packages"
            
        elif command -v dnf &> /dev/null; then
            # Fedora/RHEL
            MISSING_PACKAGES=""
            for pkg in python3-devel openssl-devel libffi-devel dbus-devel pkgconfig; do
                if ! rpm -q $pkg &> /dev/null; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done
            
            if [ -n "$MISSING_PACKAGES" ]; then
                print_warning "Installing required system packages:$MISSING_PACKAGES"
                sudo dnf install -y $MISSING_PACKAGES
            fi
            print_status "Linux system packages"
        fi
    fi
}

install_python_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Check if we're in a virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Not in a virtual environment. Recommend creating one:"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo ""
        read -p "Continue with global installation? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "Virtual environment: $VIRTUAL_ENV"
    fi
    
    # Install/upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install security dependencies
    print_info "Installing security dependencies..."
    python3 -m pip install "cryptography>=41.0.0" "keyring>=24.0.0"
    
    # Install platform-specific keyring backend
    if [ "$PLATFORM" = "Linux" ]; then
        python3 -m pip install "SecretStorage>=3.3.0"
    fi
    
    print_status "Python security dependencies installed"
}

test_keyring_support() {
    print_info "Testing native keyring support..."
    
    # Test keyring functionality
    python3 -c "
import keyring
import platform
import sys

try:
    backend = keyring.get_keyring()
    print(f'Keyring backend: {backend.__class__.__name__}')
    
    # Test store/retrieve/delete
    service = 'TraderTerminal-Test'
    username = 'test-user'
    password = 'test-password-123'
    
    # Store
    keyring.set_password(service, username, password)
    print('✅ Store: Success')
    
    # Retrieve
    retrieved = keyring.get_password(service, username)
    if retrieved == password:
        print('✅ Retrieve: Success')
    else:
        print('❌ Retrieve: Failed')
        sys.exit(1)
    
    # Delete
    keyring.delete_password(service, username)
    print('✅ Delete: Success')
    
    # Verify deletion
    deleted = keyring.get_password(service, username)
    if deleted is None:
        print('✅ Verify deletion: Success')
    else:
        print('❌ Verify deletion: Failed')
        sys.exit(1)
    
    print('✅ Native keyring fully functional')
    
except Exception as e:
    print(f'❌ Keyring test failed: {e}')
    print('⚠️  Will fallback to encrypted file storage')
    sys.exit(2)  # Special exit code for keyring failure
"
    
    KEYRING_RESULT=$?
    if [ $KEYRING_RESULT -eq 0 ]; then
        print_status "Native keyring is working"
        return 0
    elif [ $KEYRING_RESULT -eq 2 ]; then
        print_warning "Native keyring not available, will use encrypted file storage"
        return 1
    else
        print_error "Keyring test failed"
        exit 1
    fi
}

setup_credential_system() {
    print_info "Setting up TraderTerminal credential system..."
    
    # Make credential management script executable
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    chmod +x "$SCRIPT_DIR/manage_credentials.py"
    
    # Test the credential management system
    print_info "Testing credential management system..."
    
    if python3 "$SCRIPT_DIR/manage_credentials.py" test; then
        print_status "Credential management system is working"
    else
        print_error "Credential management system test failed"
        exit 1
    fi
}

migrate_existing_env() {
    # Check for existing .env files
    ENV_FILES=(
        "src/backend/.env"
        ".env"
        ".env.local"
    )
    
    for env_file in "${ENV_FILES[@]}"; do
        if [ -f "$env_file" ]; then
            print_warning "Found existing environment file: $env_file"
            read -p "Migrate credentials to secure storage? [y/N]: " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
                if python3 "$SCRIPT_DIR/manage_credentials.py" migrate --env-file "$env_file"; then
                    print_status "Migration completed"
                    print_warning "Consider removing or securing the .env file:"
                    echo "  # Backup and remove"
                    echo "  mv $env_file ${env_file}.backup"
                    echo "  # Or set secure permissions"
                    echo "  chmod 600 $env_file"
                else
                    print_error "Migration failed"
                fi
            fi
        fi
    done
}

show_next_steps() {
    print_info "Setup complete! Next steps:"
    echo ""
    echo "1. Set up your broker credentials:"
    echo "   python scripts/manage_credentials.py setup-broker --broker tastytrade"
    echo "   python scripts/manage_credentials.py setup-broker --broker data_services"
    echo ""
    echo "2. Verify your stored credentials:"
    echo "   python scripts/manage_credentials.py list"
    echo ""
    echo "3. Test a specific credential:"
    echo "   python scripts/manage_credentials.py get --key TASTYTRADE_CLIENT_SECRET"
    echo ""
    echo "4. Start the application with secure credentials:"
    echo "   cd src/backend"
    echo "   python -m uvicorn src.backend.datahub.server:app --reload"
    echo ""
    print_status "TraderTerminal secure credential system is ready!"
}

main() {
    print_header
    
    # Check system requirements
    check_dependencies
    
    # Install Python dependencies
    install_python_dependencies
    
    # Test keyring support
    test_keyring_support
    KEYRING_AVAILABLE=$?
    
    # Setup credential system
    setup_credential_system
    
    # Migrate existing credentials
    migrate_existing_env
    
    # Show next steps
    show_next_steps
    
    if [ $KEYRING_AVAILABLE -ne 0 ]; then
        echo ""
        print_warning "Note: Using encrypted file storage instead of native keyring"
        print_info "Your credentials will be stored in an encrypted file at:"
        if [ "$PLATFORM" = "Darwin" ]; then
            echo "  ~/Library/Application Support/TraderTerminal/trader_credentials.enc"
        elif [ "$PLATFORM" = "Linux" ]; then
            echo "  ~/.local/share/traderterminal/trader_credentials.enc"
        else
            echo "  ~/.traderterminal/trader_credentials.enc"
        fi
    fi
}

# Run main function
main "$@"