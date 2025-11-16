#!/bin/bash
################################################################################
# Apache HTTP Server Management Script
# 
# Ultra-minimal script-first architecture
# Supports: Fedora (RPM), Ubuntu/Debian (DEB), Arch (AUR)
# 
# Usage: apache.sh <action> [args...]
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

# Get package names for current OS
get_packages() {
    case "$OS_TYPE" in
        fedora)
            echo "httpd mod_ssl"
            ;;
        debian)
            echo "apache2 apache2-utils ssl-cert"
            ;;
        arch)
            echo "apache"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Get service name for current OS
get_service_name() {
    case "$OS_TYPE" in
        fedora)
            echo "httpd"
            ;;
        debian)
            echo "apache2"
            ;;
        arch)
            echo "httpd"
            ;;
        *)
            echo "httpd"
            ;;
    esac
}

# Get config directory
get_config_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/etc/httpd"
            ;;
        debian)
            echo "/etc/apache2"
            ;;
        arch)
            echo "/etc/httpd"
            ;;
    esac
}

# Get vhost directory
get_vhost_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/etc/httpd/conf.d"
            ;;
        debian)
            echo "/etc/apache2/sites-available"
            ;;
        arch)
            echo "/etc/httpd/conf/extra"
            ;;
    esac
}

# Get enabled vhost directory (Debian/Ubuntu only)
get_vhost_enabled_dir() {
    if [ "$OS_TYPE" = "debian" ]; then
        echo "/etc/apache2/sites-enabled"
    else
        echo ""
    fi
}

# Get log directory
get_log_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/var/log/httpd"
            ;;
        debian)
            echo "/var/log/apache2"
            ;;
        arch)
            echo "/var/log/httpd"
            ;;
    esac
}

################################################################################
# PACKAGE MANAGEMENT
################################################################################

check_package_manager_lock() {
    # Check if package manager is locked by another process
    case "$OS_TYPE" in
        debian)
            # Check if dpkg/apt is locked
            if lsof /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
               lsof /var/lib/apt/lists/lock >/dev/null 2>&1 || \
               lsof /var/cache/apt/archives/lock >/dev/null 2>&1; then
                echo "ERROR: Package manager is locked by another process."
                echo "Please wait for other package operations to complete, or run:"
                echo "  sudo killall apt apt-get dpkg"
                return 1
            fi
            ;;
        fedora)
            # Check if dnf is locked
            if [ -f /var/run/dnf.pid ]; then
                echo "ERROR: DNF is locked by another process."
                echo "Please wait for other package operations to complete."
                return 1
            fi
            ;;
        arch)
            # Check if pacman is locked
            if [ -f /var/lib/pacman/db.lck ]; then
                echo "ERROR: Pacman is locked by another process."
                echo "Please remove the lock file: sudo rm /var/lib/pacman/db.lck"
                return 1
            fi
            ;;
    esac
    return 0
}

install_packages() {
    local packages="$1"
    
    # Check if package manager is locked
    if ! check_package_manager_lock; then
        return 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            dnf install -y $packages 2>&1
            ;;
        debian)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update 2>&1
            apt-get install -y $packages 2>&1
            ;;
        arch)
            pacman -S --noconfirm $packages 2>&1
            ;;
        *)
            echo "ERROR: Unsupported OS type: $OS_TYPE"
            return 1
            ;;
    esac
}

remove_packages() {
    local packages="$1"
    
    # Check if package manager is locked
    if ! check_package_manager_lock; then
        return 1
    fi
    
    case "$OS_TYPE" in
        fedora)
            dnf remove -y $packages 2>&1
            ;;
        debian)
            export DEBIAN_FRONTEND=noninteractive
            apt-get remove -y $packages 2>&1
            local remove_status=$?
            apt-get autoremove -y 2>&1
            return $remove_status
            ;;
        arch)
            pacman -R --noconfirm $packages 2>&1
            ;;
        *)
            echo "ERROR: Unsupported OS type: $OS_TYPE"
            return 1
            ;;
    esac
}

################################################################################
# SERVICE MANAGEMENT
################################################################################

is_installed() {
    case "$OS_TYPE" in
        fedora)
            rpm -q httpd >/dev/null 2>&1
            ;;
        debian)
            dpkg -l apache2 2>/dev/null | grep -q "^ii"
            ;;
        arch)
            pacman -Q apache >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

is_running() {
    local service_name=$(get_service_name)
    systemctl is-active "$service_name" >/dev/null 2>&1
}

action_is_installed() {
    if is_installed; then
        echo "true"
        exit 0
    else
        echo "false"
        exit 0
    fi
}

action_is_running() {
    if is_running; then
        echo "true"
        exit 0
    else
        echo "false"
        exit 0
    fi
}

action_install() {
    if is_installed; then
        echo "Apache is already installed"
        exit 0
    fi
    
    echo "Installing Apache HTTP Server..."
    local packages=$(get_packages)
    
    if ! install_packages "$packages"; then
        echo "ERROR: Failed to install Apache packages"
        exit 1
    fi
    
    # Enable and start service
    local service_name=$(get_service_name)
    systemctl enable "$service_name" 2>&1
    systemctl start "$service_name" 2>&1
    
    echo "Apache installed successfully"
    
    # Auto-detect and install PHP module if PHP is available
    if [ "$OS_TYPE" = "debian" ]; then
        echo "Checking for installed PHP versions..."
        local php_found=false
        
        # Check for common PHP versions
        for version in 8.4 8.3 8.2 8.1 8.0 7.4 7.3 7.2; do
            if command -v "php$version" >/dev/null 2>&1 || [ -d "/etc/php/$version" ]; then
                echo "Found PHP $version - Installing Apache module..."
                if apt-get install -y "libapache2-mod-php$version" 2>&1; then
                    echo "PHP $version Apache module installed successfully"
                    systemctl restart "$service_name" 2>&1
                    php_found=true
                    break
                fi
            fi
        done
        
        if [ "$php_found" = false ]; then
            echo "No PHP installation detected. You can install PHP modules later."
        fi
    fi
    
    echo "Apache installation completed"
    exit 0
}

action_uninstall() {
    if ! is_installed; then
        echo "Apache is not installed"
        exit 0
    fi
    
    echo "Uninstalling Apache HTTP Server..."
    local service_name=$(get_service_name)
    
    # Stop and disable service
    systemctl stop "$service_name" 2>/dev/null || true
    systemctl disable "$service_name" 2>/dev/null || true
    
    # Remove packages
    local packages=$(get_packages)
    if ! remove_packages "$packages"; then
        echo "ERROR: Failed to uninstall Apache packages"
        exit 1
    fi
    
    echo "Apache uninstalled successfully"
    exit 0
}

action_start() {
    local service_name=$(get_service_name)
    systemctl start "$service_name" 2>&1
    echo "Apache started successfully"
    exit 0
}

action_stop() {
    local service_name=$(get_service_name)
    systemctl stop "$service_name" 2>&1
    echo "Apache stopped successfully"
    exit 0
}

action_restart() {
    local service_name=$(get_service_name)
    systemctl restart "$service_name" 2>&1
    echo "Apache restarted successfully"
    exit 0
}

action_reload() {
    local service_name=$(get_service_name)
    systemctl reload "$service_name" 2>&1
    echo "Apache configuration reloaded successfully"
    exit 0
}

action_enable() {
    local service_name=$(get_service_name)
    systemctl enable "$service_name" 2>&1
    echo "Apache autostart enabled"
    exit 0
}

action_disable() {
    local service_name=$(get_service_name)
    systemctl disable "$service_name" 2>&1
    echo "Apache autostart disabled"
    exit 0
}

################################################################################
# VIRTUAL HOST MANAGEMENT
################################################################################

action_vhost_list() {
    local vhost_dir=$(get_vhost_dir)
    local json_output=false
    
    # Check for --json flag
    if [ "$1" = "--json" ]; then
        json_output=true
    fi
    
    if [ ! -d "$vhost_dir" ]; then
        if [ "$json_output" = true ]; then
            echo "[]"
        else
            echo "No vhost directory found"
        fi
        exit 0
    fi
    
    # Find all vhost config files
    local vhosts=()
    
    if [ "$OS_TYPE" = "debian" ]; then
        # Debian/Ubuntu: Check sites-available
        for file in "$vhost_dir"/*.conf; do
            [ -f "$file" ] || continue
            local basename=$(basename "$file")
            local enabled=false
            
            # Check if enabled
            local enabled_dir=$(get_vhost_enabled_dir)
            if [ -L "$enabled_dir/$basename" ]; then
                enabled=true
            fi
            
            # Get additional info: server name, SSL, PHP
            local server_name=$(grep -m1 "ServerName" "$file" | awk '{print $2}')
            local ssl_enabled=false
            local php_version=""
            
            if grep -q "SSLEngine on" "$file"; then
                ssl_enabled=true
            fi
            
            if grep -q "php.*fpm" "$file"; then
                php_version=$(grep -oP 'php\K[0-9]+\.[0-9]+' "$file" | head -n1)
            fi
            
            vhosts+=("$basename:$enabled:$server_name:$ssl_enabled:$php_version")
        done
    else
        # Fedora/Arch: All conf.d files are enabled
        for file in "$vhost_dir"/*.conf; do
            [ -f "$file" ] || continue
            local basename=$(basename "$file")
            
            # Get additional info
            local server_name=$(grep -m1 "ServerName" "$file" | awk '{print $2}')
            local ssl_enabled=false
            local php_version=""
            
            if grep -q "SSLEngine on" "$file"; then
                ssl_enabled=true
            fi
            
            if grep -q "php.*fpm" "$file"; then
                php_version=$(grep -oP 'php\K[0-9]+\.[0-9]+' "$file" | head -n1)
            fi
            
            vhosts+=("$basename:true:$server_name:$ssl_enabled:$php_version")
        done
    fi
    
    # Output
    if [ "$json_output" = true ]; then
        echo -n "["
        local first=true
        for vhost in "${vhosts[@]}"; do
            IFS=':' read -r filename enabled server_name ssl_enabled php_version <<< "$vhost"
            if [ "$first" = true ]; then
                first=false
            else
                echo -n ","
            fi
            echo -n "{\"filename\":\"$filename\",\"enabled\":$enabled,\"server_name\":\"$server_name\",\"ssl\":$ssl_enabled,\"php_version\":\"$php_version\"}"
        done
        echo "]"
    else
        for vhost in "${vhosts[@]}"; do
            IFS=':' read -r filename enabled <<< "$vhost"
            if [ "$enabled" = true ]; then
                echo "$filename [ENABLED]"
            else
                echo "$filename [DISABLED]"
            fi
        done
    fi
    
    exit 0
}

action_vhost_create() {
    local server_name="$1"
    local document_root="$2"
    local ssl=false
    local ssl_cert=""
    local ssl_key=""
    local php_version=""
    
    # Parse optional arguments
    shift 2
    while [ $# -gt 0 ]; do
        case "$1" in
            --ssl)
                ssl=true
                shift
                ;;
            --ssl-cert)
                ssl_cert="$2"
                shift 2
                ;;
            --ssl-key)
                ssl_key="$2"
                shift 2
                ;;
            --php-version)
                php_version="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$server_name" ] || [ -z "$document_root" ]; then
        echo "ERROR: server_name and document_root are required"
        exit 1
    fi
    
    # Create document root
    mkdir -p "$document_root"
    
    # Create default index.html if not exists
    if [ ! -f "$document_root/index.html" ]; then
        cat > "$document_root/index.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>$server_name</title>
</head>
<body>
    <h1>Welcome to $server_name</h1>
    <p>This is a default page. Replace it with your content.</p>
</body>
</html>
EOF
    fi
    
    # Set permissions
    chown -R apache:apache "$document_root" 2>/dev/null || chown -R www-data:www-data "$document_root" 2>/dev/null || true
    chmod -R 755 "$document_root"
    
    # Create vhost config
    local vhost_dir=$(get_vhost_dir)
    local log_dir=$(get_log_dir)
    local config_file="$vhost_dir/${server_name}.conf"
    
    # Generate vhost configuration
    cat > "$config_file" <<EOF
<VirtualHost *:80>
    ServerName $server_name
    ServerAlias www.$server_name
    DocumentRoot $document_root
    
    <Directory $document_root>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog $log_dir/${server_name}-error.log
    CustomLog $log_dir/${server_name}-access.log combined
EOF
    
    # Add PHP-FPM configuration if specified
    if [ -n "$php_version" ]; then
        cat >> "$config_file" <<EOF
    
    # PHP-FPM Configuration
    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php${php_version}-fpm.sock|fcgi://localhost"
    </FilesMatch>
EOF
    fi
    
    echo "</VirtualHost>" >> "$config_file"
    
    # Add SSL configuration if requested
    if [ "$ssl" = true ]; then
        # Use provided certs or generate self-signed
        if [ -z "$ssl_cert" ]; then
            ssl_cert="/etc/ssl/certs/${server_name}.crt"
        fi
        if [ -z "$ssl_key" ]; then
            ssl_key="/etc/ssl/private/${server_name}.key"
        fi
        
        # Generate self-signed certificate if not exists
        if [ ! -f "$ssl_cert" ] || [ ! -f "$ssl_key" ]; then
            mkdir -p /etc/ssl/certs /etc/ssl/private
            openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=$server_name" \
                -keyout "$ssl_key" -out "$ssl_cert" 2>&1
            chmod 600 "$ssl_key"
        fi
        
        # Add SSL vhost
        cat >> "$config_file" <<EOF

<VirtualHost *:443>
    ServerName $server_name
    ServerAlias www.$server_name
    DocumentRoot $document_root
    
    SSLEngine on
    SSLCertificateFile $ssl_cert
    SSLCertificateKeyFile $ssl_key
    
    <Directory $document_root>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog $log_dir/${server_name}-ssl-error.log
    CustomLog $log_dir/${server_name}-ssl-access.log combined
EOF
        
        if [ -n "$php_version" ]; then
            cat >> "$config_file" <<EOF
    
    # PHP-FPM Configuration
    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php${php_version}-fpm.sock|fcgi://localhost"
    </FilesMatch>
EOF
        fi
        
        echo "</VirtualHost>" >> "$config_file"
    fi
    
    # Enable vhost (Debian/Ubuntu)
    if [ "$OS_TYPE" = "debian" ]; then
        a2ensite "${server_name}.conf" >/dev/null 2>&1 || {
            local enabled_dir=$(get_vhost_enabled_dir)
            ln -sf "$config_file" "$enabled_dir/${server_name}.conf"
        }
    fi
    
    # Update /etc/hosts file
    if ! grep -q "^127.0.0.1.*[[:space:]]$server_name" /etc/hosts; then
        echo "127.0.0.1    $server_name www.$server_name" >> /etc/hosts
        echo "✓ Added $server_name to /etc/hosts"
    else
        echo "✓ $server_name already exists in /etc/hosts"
    fi
    
    # Reload Apache
    local service_name=$(get_service_name)
    systemctl reload "$service_name" 2>&1
    
    echo "Virtual host created successfully: $server_name"
    exit 0
}

action_vhost_enable() {
    local filename="$1"
    
    if [ -z "$filename" ]; then
        echo "ERROR: filename is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        a2ensite "$filename" 2>&1 || {
            local vhost_dir=$(get_vhost_dir)
            local enabled_dir=$(get_vhost_enabled_dir)
            ln -sf "$vhost_dir/$filename" "$enabled_dir/$filename"
        }
        
        local service_name=$(get_service_name)
        systemctl reload "$service_name" 2>&1
        
        echo "Virtual host enabled: $filename"
    else
        echo "Virtual host is already active (not Debian/Ubuntu)"
    fi
    
    exit 0
}

action_vhost_disable() {
    local filename="$1"
    
    if [ -z "$filename" ]; then
        echo "ERROR: filename is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        a2dissite "$filename" 2>&1 || {
            local enabled_dir=$(get_vhost_enabled_dir)
            rm -f "$enabled_dir/$filename"
        }
        
        local service_name=$(get_service_name)
        systemctl reload "$service_name" 2>&1
        
        echo "Virtual host disabled: $filename"
    else
        echo "Cannot disable vhost on this OS (not Debian/Ubuntu)"
    fi
    
    exit 0
}

action_vhost_delete() {
    local filename="$1"
    
    if [ -z "$filename" ]; then
        echo "ERROR: filename is required"
        exit 1
    fi
    
    local vhost_dir=$(get_vhost_dir)
    local config_file="$vhost_dir/$filename"
    
    # Get server name before deleting config file
    local server_name=""
    if [ -f "$config_file" ]; then
        server_name=$(grep -m1 "^\s*ServerName" "$config_file" | sed 's/^\s*ServerName\s*//' | awk '{print $1}' | tr -d '"' | xargs)
    fi
    
    # Disable first (Debian/Ubuntu)
    if [ "$OS_TYPE" = "debian" ]; then
        a2dissite "$filename" 2>/dev/null || true
    fi
    
    # Delete config file
    if [ -f "$config_file" ]; then
        rm -f "$config_file"
        
        # Remove from /etc/hosts if server_name was found
        if [ -n "$server_name" ]; then
            # Remove lines containing the server name
            sed -i "/[[:space:]]$server_name\([[:space:]]\|$\)/d" /etc/hosts
            sed -i "/[[:space:]]www\.$server_name\([[:space:]]\|$\)/d" /etc/hosts
            echo "✓ Removed $server_name from /etc/hosts"
        fi
        
        local service_name=$(get_service_name)
        systemctl reload "$service_name" 2>&1
        
        echo "Virtual host deleted: $filename"
    else
        echo "Virtual host not found: $filename"
    fi
    
    exit 0
}

action_vhost_details() {
    local filename="$1"
    local json_output=false
    
    # Check for --json flag
    shift
    if [ "$1" = "--json" ]; then
        json_output=true
    fi
    
    if [ -z "$filename" ]; then
        echo "ERROR: filename is required"
        exit 1
    fi
    
    local vhost_dir=$(get_vhost_dir)
    local config_file="$vhost_dir/$filename"
    
    if [ ! -f "$config_file" ]; then
        echo "ERROR: Virtual host not found: $filename"
        exit 1
    fi
    
    # Parse config file - improved parsing
    local server_name=$(grep -m1 "^\s*ServerName" "$config_file" | sed 's/^\s*ServerName\s*//' | awk '{print $1}')
    local document_root=$(grep -m1 "^\s*DocumentRoot" "$config_file" | sed 's/^\s*DocumentRoot\s*//' | awk '{print $1}')
    local ssl_enabled=false
    local php_version=""
    
    # Clean up server_name and document_root (remove any trailing whitespace or quotes)
    server_name=$(echo "$server_name" | tr -d '"' | xargs)
    document_root=$(echo "$document_root" | tr -d '"' | xargs)
    
    # Check SSL
    if grep -q "^\s*SSLEngine\s\+on" "$config_file"; then
        ssl_enabled=true
    fi
    
    # Extract PHP version from config - improved regex
    if grep -q "php.*fpm" "$config_file"; then
        php_version=$(grep -oP 'php\K[0-9]+\.[0-9]+' "$config_file" | head -n1)
    fi
    
    # Clean up php_version
    php_version=$(echo "$php_version" | xargs)
    
    local enabled=true
    if [ "$OS_TYPE" = "debian" ]; then
        local enabled_dir=$(get_vhost_enabled_dir)
        if [ ! -L "$enabled_dir/$filename" ]; then
            enabled=false
        fi
    fi
    
    # Ensure empty strings for missing values
    [ -z "$server_name" ] && server_name=""
    [ -z "$document_root" ] && document_root=""
    [ -z "$php_version" ] && php_version=""
    
    if [ "$json_output" = true ]; then
        echo "{\"filename\":\"$filename\",\"server_name\":\"$server_name\",\"document_root\":\"$document_root\",\"ssl\":$ssl_enabled,\"php_version\":\"$php_version\",\"enabled\":$enabled}"
    else
        echo "Filename: $filename"
        echo "Server Name: $server_name"
        echo "Document Root: $document_root"
        echo "SSL: $ssl_enabled"
        echo "PHP Version: $php_version"
        echo "Enabled: $enabled"
    fi
    
    exit 0
}

action_vhost_update_php() {
    local filename="$1"
    local php_version="$2"
    
    if [ -z "$filename" ]; then
        echo "ERROR: filename is required"
        exit 1
    fi
    
    local vhost_dir=$(get_vhost_dir)
    local config_file="$vhost_dir/$filename"
    
    if [ ! -f "$config_file" ]; then
        echo "ERROR: Virtual host not found: $filename"
        exit 1
    fi
    
    # Remove existing PHP-FPM configuration (all occurrences)
    # First pass: remove PHP-FPM comment and SetHandler lines
    sed -i '/# PHP-FPM Configuration/d' "$config_file"
    sed -i '/SetHandler.*proxy:unix:.*php.*fpm/d' "$config_file"
    
    # Second pass: remove orphaned FilesMatch tags
    sed -i '/<FilesMatch \\\.php\$/d' "$config_file"
    sed -i '/<\/FilesMatch>/d' "$config_file"
    
    # If php_version is provided and not empty, add new configuration
    if [ -n "$php_version" ]; then
        # Create temporary file with new configuration
        local temp_file=$(mktemp)
        
        # Read file and insert PHP configuration before </VirtualHost>
        awk -v php_ver="$php_version" '
        /<\/VirtualHost>/ {
            print "    # PHP-FPM Configuration"
            print "    <FilesMatch \\.php$>"
            print "        SetHandler \"proxy:unix:/run/php/php" php_ver "-fpm.sock|fcgi://localhost\""
            print "    </FilesMatch>"
        }
        { print }
        ' "$config_file" > "$temp_file"
        
        mv "$temp_file" "$config_file"
        
        echo "PHP version updated to $php_version for $filename"
    else
        echo "PHP configuration removed from $filename"
    fi
    
    # Reload Apache
    local service_name=$(get_service_name)
    if systemctl reload "$service_name" 2>&1; then
        echo "Apache reloaded successfully"
        exit 0
    else
        echo "ERROR: Failed to reload Apache"
        exit 1
    fi
}

################################################################################
# PHP VERSION MANAGEMENT
################################################################################

action_php_list_versions() {
    local json_output=false
    
    if [ "$1" = "--json" ]; then
        json_output=true
    fi
    
    local versions=()
    
    # Check installed PHP versions
    if [ "$OS_TYPE" = "debian" ]; then
        for dir in /etc/php/*; do
            if [ -d "$dir" ]; then
                local version=$(basename "$dir")
                if [[ "$version" =~ ^[0-9]+\.[0-9]+$ ]]; then
                    versions+=("$version")
                fi
            fi
        done
    else
        # Fedora/Arch: Check single PHP installation
        if command -v php >/dev/null 2>&1; then
            local version=$(php -v | head -n1 | grep -oP '\d+\.\d+' | head -n1)
            if [ -n "$version" ]; then
                versions+=("$version")
            fi
        fi
    fi
    
    if [ "$json_output" = true ]; then
        echo -n "["
        local first=true
        for version in "${versions[@]}"; do
            if [ "$first" = true ]; then
                first=false
            else
                echo -n ","
            fi
            echo -n "\"$version\""
        done
        echo "]"
    else
        for version in "${versions[@]}"; do
            echo "$version"
        done
    fi
    
    exit 0
}

action_php_get_active() {
    if command -v php >/dev/null 2>&1; then
        php -v | head -n1 | grep -oP '\d+\.\d+' | head -n1
    else
        echo ""
    fi
    exit 0
}

action_php_switch() {
    local version="$1"
    
    if [ -z "$version" ]; then
        echo "ERROR: version is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        # Debian/Ubuntu: Use update-alternatives
        update-alternatives --set php "/usr/bin/php$version" 2>&1
        
        # Disable all PHP-FPM services
        systemctl list-units --type=service --state=running | grep "php.*fpm" | awk '{print $1}' | while read service; do
            systemctl stop "$service" 2>/dev/null || true
            systemctl disable "$service" 2>/dev/null || true
        done
        
        # Enable and start new version
        systemctl enable "php${version}-fpm" 2>&1
        systemctl start "php${version}-fpm" 2>&1
        
        echo "Switched to PHP $version"
    else
        echo "PHP version switching not supported on this OS"
    fi
    
    exit 0
}

################################################################################
# PHP MODULE MANAGEMENT
################################################################################

action_php_module_installed() {
    if [ "$OS_TYPE" = "debian" ]; then
        # Check if any PHP Apache module is installed
        if dpkg -l | grep -q "^ii.*libapache2-mod-php"; then
            echo "true"
        else
            echo "false"
        fi
    elif [ "$OS_TYPE" = "fedora" ]; then
        # Check if PHP module is installed
        if rpm -q php >/dev/null 2>&1; then
            echo "true"
        else
            echo "false"
        fi
    else
        echo "false"
    fi
    exit 0
}

action_php_module_list() {
    local json_output=false
    
    if [ "$1" = "--json" ]; then
        json_output=true
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        local modules=()
        
        # Find all installed PHP Apache modules
        for version in $(dpkg -l | grep "^ii.*libapache2-mod-php" | awk '{print $2}' | grep -oP 'php\K[0-9]+\.[0-9]+'); do
            local enabled=false
            
            # Check if module is enabled
            if [ -f "/etc/apache2/mods-enabled/php${version}.load" ]; then
                enabled=true
            fi
            
            modules+=("$version:$enabled")
        done
        
        if [ "$json_output" = true ]; then
            echo -n "["
            local first=true
            for mod_info in "${modules[@]}"; do
                IFS=':' read -r version enabled <<< "$mod_info"
                if [ "$first" = true ]; then
                    first=false
                else
                    echo -n ","
                fi
                echo -n "{\"version\":\"$version\",\"enabled\":$enabled}"
            done
            echo "]"
        else
            for mod_info in "${modules[@]}"; do
                IFS=':' read -r version enabled <<< "$mod_info"
                if [ "$enabled" = true ]; then
                    echo "PHP $version [ENABLED]"
                else
                    echo "PHP $version [DISABLED]"
                fi
            done
        fi
    else
        if [ "$json_output" = true ]; then
            echo "[]"
        else
            echo "PHP module listing not supported on this OS"
        fi
    fi
    exit 0
}

action_php_module_get_active() {
    if [ "$OS_TYPE" = "debian" ]; then
        # Check which PHP module is currently enabled
        for version in 8.4 8.3 8.2 8.1 8.0 7.4 7.3 7.2; do
            if [ -f "/etc/apache2/mods-enabled/php${version}.load" ]; then
                echo "$version"
                exit 0
            fi
        done
        echo ""
    else
        echo ""
    fi
    exit 0
}

action_php_module_switch() {
    local target_version="$1"
    
    if [ -z "$target_version" ]; then
        echo "ERROR: PHP version is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        # Check if target version is installed
        if ! dpkg -l | grep -q "^ii.*libapache2-mod-php${target_version}"; then
            echo "ERROR: PHP $target_version Apache module is not installed"
            exit 1
        fi
        
        # Disable all PHP modules
        for version in $(dpkg -l | grep "^ii.*libapache2-mod-php" | awk '{print $2}' | grep -oP 'php\K[0-9]+\.[0-9]+'); do
            a2dismod "php${version}" 2>/dev/null || true
        done
        
        # Enable target version
        a2enmod "php${target_version}" 2>&1
        
        # Restart Apache
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        
        echo "Switched to PHP $target_version Apache module"
    else
        echo "ERROR: PHP module switching not supported on this OS"
        exit 1
    fi
    exit 0
}

action_php_module_install() {
    local version="$1"
    
    if [ "$OS_TYPE" = "debian" ]; then
        # If no version specified, detect available PHP versions
        if [ -z "$version" ]; then
            # Try to get the highest installed PHP version
            version=$(php -v 2>/dev/null | head -n1 | grep -oP '\d+\.\d+' | head -n1)
            
            # If no PHP found, use default
            if [ -z "$version" ]; then
                version="8.3"
            fi
        fi
        
        echo "Installing PHP $version Apache module..."
        
        # Install PHP Apache module
        apt-get update -qq 2>&1
        apt-get install -y "libapache2-mod-php${version}" 2>&1
        
        # Restart Apache
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        
        echo "PHP $version Apache module installed successfully"
    elif [ "$OS_TYPE" = "fedora" ]; then
        # Fedora: Install PHP
        dnf install -y php 2>&1
        
        # Restart Apache
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        
        echo "PHP Apache module installed successfully"
    else
        echo "ERROR: PHP module installation not supported on this OS"
        exit 1
    fi
    exit 0
}

action_php_module_uninstall() {
    local version="$1"
    
    if [ "$OS_TYPE" = "debian" ]; then
        if [ -z "$version" ]; then
            # Remove all PHP Apache modules
            apt-get remove -y libapache2-mod-php* 2>&1
        else
            # Remove specific version
            apt-get remove -y "libapache2-mod-php${version}" 2>&1
        fi
        
        # Restart Apache
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        
        echo "PHP Apache module uninstalled successfully"
    elif [ "$OS_TYPE" = "fedora" ]; then
        dnf remove -y php 2>&1
        
        # Restart Apache
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        
        echo "PHP Apache module uninstalled successfully"
    else
        echo "ERROR: PHP module uninstallation not supported on this OS"
        exit 1
    fi
    exit 0
}

################################################################################
# APACHE MODULES MANAGEMENT
################################################################################

action_module_list() {
    local format="$1"
    
    if [ "$OS_TYPE" = "debian" ]; then
        # Get all available modules
        local available_modules=()
        local enabled_modules=()
        
        # List available modules
        if [ -d "/etc/apache2/mods-available" ]; then
            for mod_file in /etc/apache2/mods-available/*.load; do
                if [ -f "$mod_file" ]; then
                    local mod_name=$(basename "$mod_file" .load)
                    available_modules+=("$mod_name")
                fi
            done
        fi
        
        # List enabled modules
        if [ -d "/etc/apache2/mods-enabled" ]; then
            for mod_file in /etc/apache2/mods-enabled/*.load; do
                if [ -f "$mod_file" ]; then
                    local mod_name=$(basename "$mod_file" .load)
                    enabled_modules+=("$mod_name")
                fi
            done
        fi
        
        if [ "$format" = "--json" ]; then
            # JSON output
            echo "["
            local first=true
            for mod in "${available_modules[@]}"; do
                if [ "$first" = true ]; then
                    first=false
                else
                    echo ","
                fi
                
                local enabled=false
                for enabled_mod in "${enabled_modules[@]}"; do
                    if [ "$mod" = "$enabled_mod" ]; then
                        enabled=true
                        break
                    fi
                done
                
                # Get module description
                local description=""
                case "$mod" in
                    ssl) description="SSL/TLS support for encrypted connections" ;;
                    rewrite) description="URL rewriting engine" ;;
                    headers) description="HTTP header control" ;;
                    proxy) description="Proxy/Gateway functionality" ;;
                    proxy_http) description="HTTP proxy support" ;;
                    proxy_fcgi) description="FastCGI proxy support" ;;
                    php*) description="PHP module for Apache" ;;
                    deflate) description="Compress content before delivery" ;;
                    expires) description="Control cache expiration" ;;
                    dir) description="Directory index handling" ;;
                    mime) description="MIME type handling" ;;
                    authz_core) description="Core authorization" ;;
                    authz_host) description="Host-based authorization" ;;
                    authn_core) description="Core authentication" ;;
                    authn_file) description="File-based authentication" ;;
                    access_compat) description="Access compatibility" ;;
                    alias) description="URL aliasing" ;;
                    env) description="Environment variable control" ;;
                    filter) description="Smart filtering" ;;
                    negotiation) description="Content negotiation" ;;
                    setenvif) description="Set environment based on request" ;;
                    status) description="Server status information" ;;
                    *) description="Apache module" ;;
                esac
                
                echo -n "  {\"name\":\"$mod\",\"enabled\":$enabled,\"description\":\"$description\"}"
            done
            echo ""
            echo "]"
        else
            # Plain text output
            echo "Available Apache Modules:"
            echo "========================="
            for mod in "${available_modules[@]}"; do
                local status="[ ]"
                for enabled_mod in "${enabled_modules[@]}"; do
                    if [ "$mod" = "$enabled_mod" ]; then
                        status="[✓]"
                        break
                    fi
                done
                echo "$status $mod"
            done
        fi
    else
        echo "ERROR: Module listing not supported on this OS"
        exit 1
    fi
    exit 0
}

action_module_enable() {
    local module_name="$1"
    
    if [ -z "$module_name" ]; then
        echo "ERROR: module name is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        a2enmod "$module_name" 2>&1
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        echo "Module $module_name enabled successfully"
    else
        echo "ERROR: Module management not supported on this OS"
        exit 1
    fi
    exit 0
}

action_module_disable() {
    local module_name="$1"
    
    if [ -z "$module_name" ]; then
        echo "ERROR: module name is required"
        exit 1
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        a2dismod "$module_name" 2>&1
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        echo "Module $module_name disabled successfully"
    else
        echo "ERROR: Module management not supported on this OS"
        exit 1
    fi
    exit 0
}

################################################################################
# SSL MANAGEMENT
################################################################################

action_ssl_is_enabled() {
    if [ "$OS_TYPE" = "debian" ]; then
        if a2query -m ssl 2>/dev/null; then
            echo "true"
        else
            echo "false"
        fi
    else
        # Fedora/Arch: Check if mod_ssl is loaded
        local config_dir=$(get_config_dir)
        if grep -r "LoadModule ssl_module" "$config_dir" >/dev/null 2>&1; then
            echo "true"
        else
            echo "false"
        fi
    fi
    exit 0
}

action_ssl_enable() {
    if [ "$OS_TYPE" = "debian" ]; then
        a2enmod ssl 2>&1
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        echo "SSL module enabled"
    elif [ "$OS_TYPE" = "fedora" ]; then
        # Install mod_ssl if not installed
        if ! rpm -q mod_ssl >/dev/null 2>&1; then
            dnf install -y mod_ssl 2>&1
        fi
        local service_name=$(get_service_name)
        systemctl restart "$service_name" 2>&1
        echo "SSL module enabled"
    else
        echo "SSL module management not supported on this OS"
    fi
    exit 0
}

action_ssl_create_cert() {
    local domain="$1"
    local cert_path=""
    local key_path=""
    
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --cert-path)
                cert_path="$2"
                shift 2
                ;;
            --key-path)
                key_path="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$domain" ]; then
        echo "ERROR: domain is required"
        exit 1
    fi
    
    # Set default paths
    if [ -z "$cert_path" ]; then
        cert_path="/etc/ssl/certs/${domain}.crt"
    fi
    if [ -z "$key_path" ]; then
        key_path="/etc/ssl/private/${domain}.key"
    fi
    
    # Create directories
    mkdir -p /etc/ssl/certs /etc/ssl/private
    
    # Generate self-signed certificate
    openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$domain" \
        -keyout "$key_path" -out "$cert_path" 2>&1
    
    chmod 600 "$key_path"
    chmod 644 "$cert_path"
    
    echo "SSL certificate created:"
    echo "  Certificate: $cert_path"
    echo "  Private Key: $key_path"
    
    exit 0
}

action_ssl_trust_cert() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        echo "ERROR: domain is required"
        exit 1
    fi
    
    local cert_path="/etc/ssl/certs/${domain}.crt"
    
    # Check if certificate exists
    if [ ! -f "$cert_path" ]; then
        echo "ERROR: Certificate not found: $cert_path"
        echo "Create the certificate first with: ssl-create-cert $domain"
        exit 1
    fi
    
    case "$OS_TYPE" in
        debian)
            # Ubuntu/Debian: Copy to ca-certificates and update
            cp "$cert_path" "/usr/local/share/ca-certificates/${domain}.crt"
            update-ca-certificates 2>&1
            echo "✓ Certificate added to system trust store"
            echo "✓ Chrome and other browsers will now trust this certificate"
            echo "✓ You may need to restart your browser"
            ;;
        fedora)
            # Fedora/RHEL: Copy to pki and update
            cp "$cert_path" "/etc/pki/ca-trust/source/anchors/${domain}.crt"
            update-ca-trust 2>&1
            echo "✓ Certificate added to system trust store"
            echo "✓ Chrome and other browsers will now trust this certificate"
            echo "✓ You may need to restart your browser"
            ;;
        arch)
            # Arch: Copy to ca-certificates and update
            cp "$cert_path" "/etc/ca-certificates/trust-source/anchors/${domain}.crt"
            trust extract-compat 2>&1
            echo "✓ Certificate added to system trust store"
            echo "✓ Chrome and other browsers will now trust this certificate"
            echo "✓ You may need to restart your browser"
            ;;
        *)
            echo "ERROR: Certificate trust management not supported on this OS"
            exit 1
            ;;
    esac
    
    exit 0
}

action_ssl_untrust_cert() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        echo "ERROR: domain is required"
        exit 1
    fi
    
    case "$OS_TYPE" in
        debian)
            rm -f "/usr/local/share/ca-certificates/${domain}.crt"
            update-ca-certificates 2>&1
            echo "✓ Certificate removed from system trust store"
            ;;
        fedora)
            rm -f "/etc/pki/ca-trust/source/anchors/${domain}.crt"
            update-ca-trust 2>&1
            echo "✓ Certificate removed from system trust store"
            ;;
        arch)
            rm -f "/etc/ca-certificates/trust-source/anchors/${domain}.crt"
            trust extract-compat 2>&1
            echo "✓ Certificate removed from system trust store"
            ;;
        *)
            echo "ERROR: Certificate trust management not supported on this OS"
            exit 1
            ;;
    esac
    
    exit 0
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
        # Service management
        is-installed)       action_is_installed ;;
        is-running)         action_is_running ;;
        install)            action_install ;;
        uninstall)          action_uninstall ;;
        start)              action_start ;;
        stop)               action_stop ;;
        restart)            action_restart ;;
        reload)             action_reload ;;
        enable)             action_enable ;;
        disable)            action_disable ;;
        
        # Virtual host management
        vhost-list)         action_vhost_list "$@" ;;
        vhost-create)       action_vhost_create "$@" ;;
        vhost-enable)       action_vhost_enable "$@" ;;
        vhost-disable)      action_vhost_disable "$@" ;;
        vhost-delete)       action_vhost_delete "$@" ;;
        vhost-details)      action_vhost_details "$@" ;;
        vhost-update-php)   action_vhost_update_php "$@" ;;
        
        # Module management
        module-list)        action_module_list "$@" ;;
        module-enable)      action_module_enable "$@" ;;
        module-disable)     action_module_disable "$@" ;;
        
        # PHP management
        php-list-versions)       action_php_list_versions "$@" ;;
        php-get-active)          action_php_get_active ;;
        php-switch)              action_php_switch "$@" ;;
        php-module-installed)    action_php_module_installed ;;
        php-module-list)         action_php_module_list "$@" ;;
        php-module-get-active)   action_php_module_get_active ;;
        php-module-switch)       action_php_module_switch "$@" ;;
        php-module-install)      action_php_module_install "$@" ;;
        php-module-uninstall)    action_php_module_uninstall "$@" ;;
        
        # SSL management
        ssl-is-enabled)     action_ssl_is_enabled ;;
        ssl-enable)         action_ssl_enable ;;
        ssl-create-cert)    action_ssl_create_cert "$@" ;;
        ssl-trust-cert)     action_ssl_trust_cert "$@" ;;
        ssl-untrust-cert)   action_ssl_untrust_cert "$@" ;;
        
        # Help
        --help|help)
            cat <<EOF
Apache HTTP Server Management Script

USAGE: apache.sh <action> [args...]

SERVICE MANAGEMENT:
  is-installed              Check if Apache is installed
  is-running                Check if Apache is running
  install                   Install Apache
  uninstall                 Uninstall Apache
  start                     Start Apache service
  stop                      Stop Apache service
  restart                   Restart Apache service
  reload                    Reload Apache configuration
  enable                    Enable Apache autostart
  disable                   Disable Apache autostart

MODULE MANAGEMENT:
  module-list [--json]      List all Apache modules with status
  module-enable <module>    Enable an Apache module
  module-disable <module>   Disable an Apache module

VIRTUAL HOST MANAGEMENT:
  vhost-list [--json]                           List all virtual hosts
  vhost-create <domain> <docroot> [--ssl]       Create new virtual host
  vhost-enable <filename>                       Enable virtual host
  vhost-disable <filename>                      Disable virtual host
  vhost-delete <filename>                       Delete virtual host
  vhost-details <filename> [--json]             Show virtual host details
  vhost-update-php <filename> <version>         Update PHP version for vhost

PHP MANAGEMENT:
  php-list-versions [--json]    List installed PHP versions (system-wide)
  php-get-active                Get active PHP CLI version
  php-switch <version>          Switch PHP CLI version
  
PHP APACHE MODULE MANAGEMENT:
  php-module-installed          Check if any PHP Apache module is installed
  php-module-list [--json]      List installed PHP Apache modules
  php-module-get-active         Get currently active PHP Apache module
  php-module-switch <version>   Switch active PHP Apache module
  php-module-install [version]  Install PHP Apache module
  php-module-uninstall [ver]    Uninstall PHP Apache module

SSL MANAGEMENT:
  ssl-is-enabled                Check if SSL module is enabled
  ssl-enable                    Enable SSL module
  ssl-create-cert <domain>      Create self-signed SSL certificate
  ssl-trust-cert <domain>       Add certificate to system trust store (fix browser warnings)
  ssl-untrust-cert <domain>     Remove certificate from system trust store

EXAMPLES:
  # Install Apache
  sudo ./apache.sh install
  
  # Create a virtual host
  sudo ./apache.sh vhost-create example.com /var/www/example
  
  # Create a virtual host with SSL
  sudo ./apache.sh vhost-create example.com /var/www/example --ssl
  
  # List all virtual hosts
  ./apache.sh vhost-list --json
  
  # Switch PHP version
  sudo ./apache.sh php-switch 8.2

EOF
            exit 0
            ;;
        
        *)
            echo "ERROR: Unknown action: $action"
            echo "Use 'apache.sh --help' for usage information"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
