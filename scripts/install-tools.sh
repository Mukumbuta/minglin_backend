#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to install Docker
install_docker() {
    print_status "Checking Docker installation..."
    
    if command_exists docker; then
        print_success "Docker is already installed: $(docker --version)"
        return 0
    fi
    
    print_status "Installing Docker..."
    OS=$(detect_os)
    
    case $OS in
        "ubuntu")
            # Install Docker on Ubuntu
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            sudo usermod -aG docker $USER
            print_success "Docker installed successfully. Please log out and log back in for group changes to take effect."
            ;;
        "centos")
            # Install Docker on CentOS
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            print_success "Docker installed successfully. Please log out and log back in for group changes to take effect."
            ;;
        "macos")
            print_warning "Please install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop"
            return 1
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            return 1
            ;;
    esac
}

# Function to install Docker Compose
install_docker_compose() {
    print_status "Checking Docker Compose installation..."
    
    if command_exists "docker compose"; then
        print_success "Docker Compose is already installed: $(docker compose version)"
        return 0
    fi
    
    print_status "Installing Docker Compose..."
    
    # Install Docker Compose v2 (included with Docker Desktop or Docker Engine)
    if command_exists docker; then
        # Check if compose plugin is available
        if docker compose version >/dev/null 2>&1; then
            print_success "Docker Compose v2 is available via 'docker compose'"
            return 0
        fi
    fi
    
    # Fallback to installing docker-compose v1
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose installed successfully"
}

# Function to install Make
install_make() {
    print_status "Checking Make installation..."
    
    if command_exists make; then
        print_success "Make is already installed: $(make --version | head -n1)"
        return 0
    fi
    
    print_status "Installing Make..."
    OS=$(detect_os)
    
    case $OS in
        "ubuntu")
            sudo apt-get update && sudo apt-get install -y make
            ;;
        "centos")
            sudo yum install -y make
            ;;
        "macos")
            # Make is usually pre-installed on macOS
            print_warning "Make should be pre-installed on macOS. Please install Xcode Command Line Tools: xcode-select --install"
            return 1
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            return 1
            ;;
    esac
    
    print_success "Make installed successfully"
}

# Function to verify installations
verify_installations() {
    print_status "Verifying installations..."
    
    local all_good=true
    
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        all_good=false
    fi
    
    if ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed or not in PATH"
        all_good=false
    fi
    
    if ! command_exists make; then
        print_error "Make is not installed or not in PATH"
        all_good=false
    fi
    
    if [ "$all_good" = true ]; then
        print_success "All required tools are installed and available!"
        echo ""
        echo "Installed versions:"
        echo "  Docker: $(docker --version)"
        echo "  Docker Compose: $(docker compose version)"
        echo "  Make: $(make --version | head -n1)"
    else
        print_error "Some tools are missing. Please run the installation again."
        return 1
    fi
}

# Main installation function
main() {
    echo "🚀 Setting up development environment for minglin_backend"
    echo "=================================================="
    echo ""
    
    install_docker
    install_docker_compose
    install_make
    verify_installations
    
    echo ""
    echo "🎉 Setup complete! You can now run:"
    echo "  make dev-setup    # Start the development environment"
    echo "  make dev-start    # Start the API and database"
    echo "  make dev-stop     # Stop all services"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 