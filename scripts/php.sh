#!/bin/bash
################################################################################
# PHP Management Script
# 
# Multi-version PHP management with extension and FPM support
# Supports: Fedora (RPM), Ubuntu/Debian (DEB), Arch (AUR)
# 
# Usage: php.sh <action> [args...]
################################################################################

set -e  # Exit on error

################################################################################
# OS DETECTION & CONFIGURATION
################################################################################

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID="$ID"
        OS_VERSION="$VERSION_ID"
    elif [ -f /etc/fedora-release ]; then
        OS_ID="fedora"
    elif [ -f /etc/debian_version ]; then
        OS_ID="debian"
    else
        OS_ID="unknown"
    fi
    
    # Normalize OS ID
    case "$OS_ID" in
        fedora|rhel|centos|rocky|almalinux)
            OS_TYPE="fedora"
            ;;
        ubuntu|debian|linuxmint|pop)
            OS_TYPE="debian"
            ;;
        arch|manjaro|endeavouros)
            OS_TYPE="arch"
            ;;
        *)
            OS_TYPE="unknown"
            ;;
    esac
    
    export OS_TYPE
}

# Get available PHP versions for current OS
get_available_versions() {
    case "$OS_TYPE" in
        fedora)
            echo "7.4 8.0 8.1 8.2 8.3"
            ;;
        debian)
            echo "7.4 8.0 8.1 8.2 8.3"
            ;;
        arch)
            echo "8.2 8.3"  # Arch typically has latest versions
            ;;
        *)
            echo "8.2"
            ;;
    esac
}

# Get PHP package name for version
get_php_package() {
    local version="$1"
    case "$OS_TYPE" in
        fedora)
            echo "php${version//./}"  # php82, php83 etc
            ;;
        debian)
            echo "php$version"  # php8.2, php8.3 etc
            ;;
        arch)
            if [ "$version" = "8.2" ] || [ "$version" = "8.3" ]; then
                echo "php"
            else
                echo "php$version"
            fi
            ;;
    esac
}

# Get PHP-FPM service name for version
get_fpm_service_name() {
    local version="$1"
    case "$OS_TYPE" in
        fedora)
            echo "php${version//./}-php-fpm"
            ;;
        debian)
            echo "php$version-fpm"
            ;;
        arch)
            echo "php-fpm"
            ;;
    esac
}

# Get PHP config directory for version
get_php_config_dir() {
    local version="$1"
    case "$OS_TYPE" in
        fedora)
            echo "/etc/php/${version//./}"
            ;;
        debian)
            echo "/etc/php/$version"
            ;;
        arch)
            echo "/etc/php"
            ;;
    esac
}

# Get PHP extension directory for version
get_php_extension_dir() {
    local version="$1"
    case "$OS_TYPE" in
        fedora)
            echo "/usr/lib64/php/${version//./}/modules"
            ;;
        debian)
            echo "/usr/lib/php/$(date +%Y%m%d)"  # Debian uses date-based dirs
            ;;
        arch)
            echo "/usr/lib/php/modules"
            ;;
    esac
}

################################################################################
# PACKAGE MANAGEMENT
################################################################################

check_package_manager_lock() {
    case "$OS_TYPE" in
        debian)
            if lsof /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
               lsof /var/lib/apt/lists/lock >/dev/null 2>&1 || \
               lsof /var/cache/apt/archives/lock >/dev/null 2>&1; then
                echo "ERROR: Package manager is locked by another process"
                exit 1
            fi
            ;;
        fedora)
            if [ -f /var/run/dnf.pid ] || [ -f /var/run/yum.pid ]; then
                echo "ERROR: Package manager is locked by another process"
                exit 1
            fi
            ;;
    esac
}

install_packages() {
    local packages="$1"
    check_package_manager_lock
    
    case "$OS_TYPE" in
        fedora)
            dnf install -y $packages
            ;;
        debian)
            apt-get update -qq
            DEBIAN_FRONTEND=noninteractive apt-get install -y $packages
            ;;
        arch)
            pacman -S --noconfirm $packages
            ;;
        *)
            echo "ERROR: Unsupported OS type: $OS_TYPE"
            exit 1
            ;;
    esac
}

uninstall_packages() {
    local packages="$1"
    check_package_manager_lock
    
    case "$OS_TYPE" in
        fedora)
            dnf remove -y $packages
            ;;
        debian)
            apt-get remove -y --purge $packages
            apt-get autoremove -y
            ;;
        arch)
            pacman -Rns --noconfirm $packages
            ;;
        *)
            echo "ERROR: Unsupported OS type: $OS_TYPE"
            exit 1
            ;;
    esac
}

################################################################################
# VERSION MANAGEMENT
################################################################################

action_version_list_installed() {
    local json_output=false
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --json)
                json_output=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    local versions=()
    case "$OS_TYPE" in
        fedora)
            for version in $(get_available_versions); do
                local pkg=$(get_php_package "$version")
                if rpm -q "$pkg" >/dev/null 2>&1; then
                    versions+=("$version")
                fi
            done
            ;;
        debian)
            for version in $(get_available_versions); do
                local pkg=$(get_php_package "$version")
                # Check for CLI package which is the main indicator
                if dpkg -l "${pkg}-cli" 2>/dev/null | grep -q "^ii\|^iU\|^iF\|^iH"; then
                    versions+=("$version")
                fi
            done
            ;;
        arch)
            if pacman -Q php >/dev/null 2>&1; then
                # Get version from installed package
                local installed_version=$(php --version 2>/dev/null | head -n1 | awk '{print $2}' | cut -d. -f1,2)
                if [ -n "$installed_version" ]; then
                    versions+=("$installed_version")
                fi
            fi
            ;;
    esac
    
    if [ "$json_output" = true ]; then
        printf "["
        for i in "${!versions[@]}"; do
            [ $i -gt 0 ] && printf ","
            printf "\"%s\"" "${versions[$i]}"
        done
        printf "]"
    else
        printf "%s\n" "${versions[@]}"
    fi
}

action_version_list_available() {
    local json_output=false
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --json)
                json_output=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    local versions=$(get_available_versions)
    
    if [ "$json_output" = true ]; then
        echo "$versions" | tr ' ' '\n' | sed 's/^/"/; s/$/",/' | tr -d '\n' | sed 's/,$//; s/^/[/; s/$/**]/' | tr '*' '\n'
    else
        echo "$versions" | tr ' ' '\n'
    fi
}

action_version_get_active() {
    if command -v php >/dev/null 2>&1; then
        php --version 2>/dev/null | head -n1 | awk '{print $2}' | cut -d. -f1,2
    else
        echo ""
    fi
}

action_version_install() {
    local version="$1"
    
    if [ -z "$version" ]; then
        echo "ERROR: PHP version is required"
        exit 1
    fi
    
    # Check if version is available
    local available_versions=$(get_available_versions)
    if ! echo "$available_versions" | grep -wq "$version"; then
        echo "ERROR: PHP version $version is not available for $OS_TYPE"
        echo "Available versions: $available_versions"
        exit 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            local pkg=$(get_php_package "$version")
            local packages="$pkg ${pkg}-cli ${pkg}-fpm ${pkg}-common ${pkg}-mbstring ${pkg}-xml ${pkg}-mysqlnd ${pkg}-gd ${pkg}-curl ${pkg}-zip"
            echo "Installing PHP $version packages: $packages"
            install_packages "$packages"
            ;;
        debian)
            # Add Ondrej's PPA for multiple PHP versions
            if ! grep -q "ondrej/php" /etc/apt/sources.list.d/* 2>/dev/null; then
                apt-get update -qq
                apt-get install -y software-properties-common
                add-apt-repository -y ppa:ondrej/php
                apt-get update -qq
            fi
            
            local pkg=$(get_php_package "$version")
            local packages="$pkg ${pkg}-cli ${pkg}-fpm ${pkg}-common ${pkg}-mbstring ${pkg}-xml ${pkg}-mysql ${pkg}-gd ${pkg}-curl ${pkg}-zip ${pkg}-dev"
            echo "Installing PHP $version packages: $packages"
            install_packages "$packages"
            
            # Set up alternatives after installation
            if [ -f "/usr/bin/php$version" ]; then
                update-alternatives --install /usr/bin/php php "/usr/bin/php$version" 50 2>/dev/null || true
                
                # Install php-config alternative if available
                if [ -f "/usr/bin/php-config$version" ]; then
                    update-alternatives --install /usr/bin/php-config php-config "/usr/bin/php-config$version" 50 2>/dev/null || true
                fi
                
                # Install phpize alternative if available
                if [ -f "/usr/bin/phpize$version" ]; then
                    update-alternatives --install /usr/bin/phpize phpize "/usr/bin/phpize$version" 50 2>/dev/null || true
                fi
            fi
            ;;
        arch)
            if [ "$version" = "8.2" ] || [ "$version" = "8.3" ]; then
                local packages="php php-fpm"
                echo "Installing PHP packages: $packages"
                install_packages "$packages"
            else
                echo "ERROR: PHP version $version is not available in Arch repositories"
                exit 1
            fi
            ;;
    esac
    
    echo "PHP $version installed successfully"
}

action_version_uninstall() {
    local version="$1"
    
    if [ -z "$version" ]; then
        echo "ERROR: PHP version is required"
        exit 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            local pkg=$(get_php_package "$version")
            # Stop FPM service first
            local fpm_service=$(get_fpm_service_name "$version")
            systemctl stop "$fpm_service" 2>/dev/null || true
            
            # Find all related packages
            local packages=$(rpm -qa | grep "^${pkg}-" | tr '\n' ' ')
            if [ -n "$packages" ]; then
                echo "Uninstalling PHP $version packages: $packages"
                uninstall_packages "$packages"
            fi
            ;;
        debian)
            local pkg=$(get_php_package "$version")
            # Stop FPM service first
            local fpm_service=$(get_fpm_service_name "$version")
            systemctl stop "$fpm_service" 2>/dev/null || true
            
            # Find all related packages
            local packages=$(dpkg -l | grep "^ii.*${pkg}" | awk '{print $2}' | tr '\n' ' ')
            if [ -n "$packages" ]; then
                echo "Uninstalling PHP $version packages: $packages"
                uninstall_packages "$packages"
            fi
            ;;
        arch)
            echo "Uninstalling PHP packages"
            systemctl stop php-fpm 2>/dev/null || true
            uninstall_packages "php php-fpm"
            ;;
    esac
    
    echo "PHP $version uninstalled successfully"
}

action_version_switch() {
    local version="$1"
    
    if [ -z "$version" ]; then
        echo "ERROR: PHP version is required"
        exit 1
    fi
    
    # Check if version is installed
    local installed_versions=$(action_version_list_installed)
    if ! echo "$installed_versions" | grep -wq "$version"; then
        echo "ERROR: PHP version $version is not installed"
        echo "Installed versions: $installed_versions"
        exit 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            # Switch using alternatives
            local php_bin="/usr/bin/php${version//./}"
            if [ -f "$php_bin" ]; then
                alternatives --install /usr/bin/php php "$php_bin" 50
                alternatives --set php "$php_bin"
            fi
            ;;
        debian)
            # Use update-alternatives - first install alternatives if not exists
            if command -v update-alternatives >/dev/null 2>&1; then
                # PHP binary
                if [ -f "/usr/bin/php$version" ]; then
                    update-alternatives --install /usr/bin/php php "/usr/bin/php$version" 50 2>/dev/null || true
                    update-alternatives --set php "/usr/bin/php$version" 2>/dev/null || true
                fi
                
                # PHP-config (only if exists)
                if [ -f "/usr/bin/php-config$version" ]; then
                    update-alternatives --install /usr/bin/php-config php-config "/usr/bin/php-config$version" 50 2>/dev/null || true
                    update-alternatives --set php-config "/usr/bin/php-config$version" 2>/dev/null || true
                else
                    echo "📢 php-config$version not found, skipping alternatives setup"
                fi
                
                # PHPize (only if exists) 
                if [ -f "/usr/bin/phpize$version" ]; then
                    update-alternatives --install /usr/bin/phpize phpize "/usr/bin/phpize$version" 50 2>/dev/null || true
                    update-alternatives --set phpize "/usr/bin/phpize$version" 2>/dev/null || true
                else
                    echo "📢 phpize$version not found, skipping alternatives setup"
                fi
            fi
            ;;
        arch)
            # Arch typically has only one PHP version
            echo "PHP version switching not needed on Arch Linux"
            ;;
    esac
    
    echo "Switched to PHP $version"
}

################################################################################
# EXTENSION MANAGEMENT
################################################################################

action_extension_list() {
    local json_output=false
    local version=""
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --json)
                json_output=true
                shift
                ;;
            --version)
                version="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Use specific version or active version
    local php_cmd="php"
    if [ -n "$version" ]; then
        case "$OS_TYPE" in
            fedora)
                php_cmd="/usr/bin/php${version//./}"
                ;;
            debian)
                php_cmd="/usr/bin/php$version"
                ;;
        esac
    fi
    
    if ! command -v "$php_cmd" >/dev/null 2>&1; then
        if [ "$json_output" = true ]; then
            echo "[]"
        fi
        return 0
    fi
    
    local extensions=$("$php_cmd" -m 2>/dev/null | grep -v "^\[" | sort)
    
    if [ "$json_output" = true ]; then
        # Simple JSON array formatting
        echo "$extensions" | grep -v '^$' | sed 's/^/"/; s/$/",/' | tr -d '\n' | sed 's/,$//; s/^/[/; s/$/**]/' | tr '*' '\n'
    else
        echo "$extensions"
    fi
}

action_extension_install() {
    local extension="$1"
    local version=""
    
    # Parse remaining arguments
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --version)
                version="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$extension" ]; then
        echo "ERROR: Extension name is required"
        exit 1
    fi
    
    # Use active version if not specified
    if [ -z "$version" ]; then
        version=$(action_version_get_active)
    fi
    
    if [ -z "$version" ]; then
        echo "ERROR: No PHP version specified or active"
        exit 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            local pkg_base=$(get_php_package "$version")
            local extension_pkg="${pkg_base}-${extension}"
            echo "Installing PHP extension: $extension_pkg"
            install_packages "$extension_pkg"
            ;;
        debian)
            local pkg_base=$(get_php_package "$version")
            local extension_pkg="${pkg_base}-${extension}"
            echo "Installing PHP extension: $extension_pkg"
            install_packages "$extension_pkg"
            ;;
        arch)
            echo "Installing PHP extension: php-$extension"
            install_packages "php-$extension"
            ;;
    esac
    
    echo "PHP extension '$extension' installed for version $version"
}

action_extension_uninstall() {
    local extension="$1"
    local version=""
    
    # Parse remaining arguments
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --version)
                version="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$extension" ]; then
        echo "ERROR: Extension name is required"
        exit 1
    fi
    
    # Use active version if not specified
    if [ -z "$version" ]; then
        version=$(action_version_get_active)
    fi
    
    if [ -z "$version" ]; then
        echo "ERROR: No PHP version specified or active"
        exit 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            local pkg_base=$(get_php_package "$version")
            local extension_pkg="${pkg_base}-${extension}"
            echo "Uninstalling PHP extension: $extension_pkg"
            uninstall_packages "$extension_pkg"
            ;;
        debian)
            local pkg_base=$(get_php_package "$version")
            local extension_pkg="${pkg_base}-${extension}"
            echo "Uninstalling PHP extension: $extension_pkg"
            uninstall_packages "$extension_pkg"
            ;;
        arch)
            echo "Uninstalling PHP extension: php-$extension"
            uninstall_packages "php-$extension"
            ;;
    esac
    
    echo "PHP extension '$extension' uninstalled for version $version"
}

################################################################################
# SERVICE MANAGEMENT (PHP-FPM)
################################################################################

action_is_installed() {
    local installed_versions=$(action_version_list_installed)
    if [ -n "$installed_versions" ]; then
        echo "true"
    else
        echo "false"
    fi
}

action_install() {
    # Install default version (8.2)
    action_version_install "8.2"
}

action_uninstall() {
    local installed_versions=$(action_version_list_installed)
    for version in $installed_versions; do
        action_version_uninstall "$version"
    done
    echo "All PHP versions uninstalled"
}

action_is_running() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "false"
        return 0
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    if systemctl is-active --quiet "$fpm_service" 2>/dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

action_start() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "ERROR: No active PHP version found"
        exit 1
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    systemctl start "$fpm_service"
    echo "PHP-FPM started for version $version"
}

action_stop() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "ERROR: No active PHP version found"
        exit 1
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    systemctl stop "$fpm_service"
    echo "PHP-FPM stopped for version $version"
}

action_restart() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "ERROR: No active PHP version found"
        exit 1
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    systemctl restart "$fpm_service"
    echo "PHP-FPM restarted for version $version"
}

action_enable() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "ERROR: No active PHP version found"
        exit 1
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    systemctl enable "$fpm_service"
    echo "PHP-FPM enabled for autostart (version $version)"
}

action_disable() {
    local version=$(action_version_get_active)
    if [ -z "$version" ]; then
        echo "ERROR: No active PHP version found"
        exit 1
    fi
    
    local fpm_service=$(get_fpm_service_name "$version")
    systemctl disable "$fpm_service"
    echo "PHP-FPM disabled from autostart (version $version)"
}

################################################################################
# CONFIGURATION MANAGEMENT
################################################################################

action_config_show() {
    local version=""
    local ini_file=""
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --version)
                version="$2"
                shift 2
                ;;
            --ini)
                ini_file="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Use active version if not specified
    if [ -z "$version" ]; then
        version=$(action_version_get_active)
    fi
    
    if [ -z "$version" ]; then
        echo "ERROR: No PHP version specified or active"
        exit 1
    fi
    
    # Show php.ini location and key settings
    local php_cmd="php"
    case "$OS_TYPE" in
        fedora)
            php_cmd="/usr/bin/php${version//./}"
            ;;
        debian)
            php_cmd="/usr/bin/php$version"
            ;;
    esac
    
    if command -v "$php_cmd" >/dev/null 2>&1; then
        echo "PHP $version Configuration:"
        echo "  Config File: $("$php_cmd" --ini | grep "Loaded Configuration File" | cut -d: -f2 | xargs)"
        echo "  Extension Dir: $("$php_cmd" -i 2>/dev/null | grep "extension_dir" | head -1 | cut -d= -f2 | xargs)"
        echo "  Memory Limit: $("$php_cmd" -r "echo ini_get('memory_limit');" 2>/dev/null)"
        echo "  Max Execution Time: $("$php_cmd" -r "echo ini_get('max_execution_time');" 2>/dev/null)"
        echo "  Upload Max Size: $("$php_cmd" -r "echo ini_get('upload_max_filesize');" 2>/dev/null)"
    fi
}

################################################################################
# INFO & STATUS
################################################################################

action_info() {
    local json_output=false
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --json)
                json_output=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    local is_installed=$(action_is_installed)
    local is_running=$(action_is_running)
    local active_version=$(action_version_get_active)
    local installed_versions=$(action_version_list_installed --json)
    local available_versions=$(action_version_list_available --json)
    
    if [ "$json_output" = true ]; then
        cat <<EOF
{
    "installed": $is_installed,
    "running": $is_running,
    "active_version": "${active_version:-null}",
    "installed_versions": $installed_versions,
    "available_versions": $available_versions
}
EOF
    else
        echo "PHP Status:"
        echo "  Installed: $is_installed"
        echo "  Running: $is_running"
        echo "  Active Version: ${active_version:-none}"
        echo "  Installed Versions: $(echo "$installed_versions" | tr -d '[]",' | tr ' ' '\n' | grep -v '^$' | tr '\n' ' ')"
        echo "  Available Versions: $(echo "$available_versions" | tr -d '[]",' | tr ' ' '\n' | grep -v '^$' | tr '\n' ' ')"
    fi
}

################################################################################
# MAIN
################################################################################

main() {
    # Detect OS first
    detect_os
    
    if [ "$OS_TYPE" = "unknown" ]; then
        echo "ERROR: Unsupported operating system"
        exit 1
    fi
    
    # Get action
    local action="$1"
    shift || true
    
    case "$action" in
        # Basic service management
        is-installed)               action_is_installed ;;
        is-running)                 action_is_running ;;
        install)                    action_install ;;
        uninstall)                  action_uninstall ;;
        start)                      action_start ;;
        stop)                       action_stop ;;
        restart)                    action_restart ;;
        enable)                     action_enable ;;
        disable)                    action_disable ;;
        
        # Version management
        version-list-installed)     action_version_list_installed "$@" ;;
        version-list-available)     action_version_list_available "$@" ;;
        version-get-active)         action_version_get_active ;;
        version-install)            action_version_install "$@" ;;
        version-uninstall)          action_version_uninstall "$@" ;;
        version-switch)             action_version_switch "$@" ;;
        
        # Extension management
        extension-list)             action_extension_list "$@" ;;
        extension-install)          action_extension_install "$@" ;;
        extension-uninstall)        action_extension_uninstall "$@" ;;
        
        # Configuration
        config-show)                action_config_show "$@" ;;
        
        # Info & Status
        info)                       action_info "$@" ;;
        
        # Help
        --help|help)
            cat <<EOF
PHP Management Script

USAGE: php.sh <action> [args...]

BASIC SERVICE MANAGEMENT:
  is-installed                          Check if PHP is installed
  is-running                            Check if PHP-FPM is running
  install                               Install default PHP version (8.2)
  uninstall                             Uninstall all PHP versions
  start                                 Start PHP-FPM service
  stop                                  Stop PHP-FPM service  
  restart                               Restart PHP-FPM service
  enable                                Enable PHP-FPM autostart
  disable                               Disable PHP-FPM autostart

VERSION MANAGEMENT:
  version-list-installed [--json]       List installed PHP versions
  version-list-available [--json]       List available PHP versions
  version-get-active                    Get active PHP version
  version-install <version>             Install specific PHP version
  version-uninstall <version>           Uninstall specific PHP version
  version-switch <version>              Switch active PHP version

EXTENSION MANAGEMENT:
  extension-list [--json] [--version <ver>]     List installed extensions
  extension-install <ext> [--version <ver>]     Install PHP extension
  extension-uninstall <ext> [--version <ver>]   Uninstall PHP extension

CONFIGURATION:
  config-show [--version <ver>]         Show PHP configuration info

INFO & STATUS:
  info [--json]                         Show comprehensive PHP status

EXAMPLES:
  # Install PHP 8.2
  sudo ./php.sh version-install 8.2
  
  # Install extension for specific version
  sudo ./php.sh extension-install mbstring --version 8.2
  
  # Switch PHP version
  sudo ./php.sh version-switch 8.3
  
  # List installed extensions
  ./php.sh extension-list --json
  
  # Show PHP info
  ./php.sh info --json

EOF
            exit 0
            ;;
        
        *)
            echo "ERROR: Unknown action: $action"
            echo "Use 'php.sh --help' for usage information"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
