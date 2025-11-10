#!/bin/bash
################################################################################
# MySQL Database Server Management Script
# 
# Ultra-minimal script-first architecture
# Supports: Fedora (RPM), Ubuntu/Debian (DEB), Arch (AUR)
# 
# Usage: mysql.sh <action> [args...]
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
            echo "mysql-server mysql"
            ;;
        debian)
            echo "mysql-server mysql-client"
            ;;
        arch)
            echo "mysql"
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
            echo "mysqld"
            ;;
        debian)
            echo "mysql"
            ;;
        arch)
            echo "mysqld"
            ;;
        *)
            echo "mysqld"
            ;;
    esac
}

# Get config directory
get_config_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/etc/mysql"
            ;;
        debian)
            echo "/etc/mysql"
            ;;
        arch)
            echo "/etc/mysql"
            ;;
    esac
}

# Get data directory
get_data_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/var/lib/mysql"
            ;;
        debian)
            echo "/var/lib/mysql"
            ;;
        arch)
            echo "/var/lib/mysql"
            ;;
    esac
}

# Get log directory
get_log_dir() {
    case "$OS_TYPE" in
        fedora)
            echo "/var/log/mysqld.log"
            ;;
        debian)
            echo "/var/log/mysql"
            ;;
        arch)
            echo "/var/log/mysqld.log"
            ;;
    esac
}

# Get MySQL socket path
get_socket_path() {
    case "$OS_TYPE" in
        fedora)
            echo "/var/lib/mysql/mysql.sock"
            ;;
        debian)
            echo "/var/run/mysqld/mysqld.sock"
            ;;
        arch)
            echo "/run/mysqld/mysqld.sock"
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
                echo "ERROR: Package manager is locked by another process"
                echo "Please wait for other package operations to complete"
                exit 1
            fi
            ;;
        fedora)
            # Check if dnf/yum is locked
            if [ -f /var/run/dnf.pid ] || [ -f /var/run/yum.pid ]; then
                echo "ERROR: Package manager is locked by another process"
                echo "Please wait for other package operations to complete"
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
# MYSQL CONFIGURATION HELPERS
################################################################################

configure_mysql_for_clients() {
    echo "Setting up MySQL configuration for client applications..."
    
    # Configure client configuration
    local client_config="/etc/mysql/mysql.conf.d/mysql.cnf"
    if [ -f "$client_config" ]; then
        echo "Updating MySQL client configuration..."
        cat > "$client_config" << 'EOF'
#
# The MySQL database client configuration file
#
# Ref to https://dev.mysql.com/doc/refman/en/mysql-command-options.html

[mysql]
socket = /var/run/mysqld/mysqld.sock
port = 3306

[mysqldump]
socket = /var/run/mysqld/mysqld.sock

[client]
socket = /var/run/mysqld/mysqld.sock
port = 3306
EOF
    fi
    
    # Enable socket and port in server configuration
    local server_config="/etc/mysql/mysql.conf.d/mysqld.cnf"
    if [ -f "$server_config" ]; then
        echo "Updating MySQL server configuration..."
        # Enable socket line
        sed -i 's/^# socket.*= \/var\/run\/mysqld\/mysqld.sock/socket        = \/var\/run\/mysqld\/mysqld.sock/' "$server_config"
        # Enable port line  
        sed -i 's/^# port.*= 3306/port          = 3306/' "$server_config"
    fi
    
    # Create socket symlink for legacy applications
    echo "Creating socket symlink for compatibility..."
    ln -sf /var/run/mysqld/mysqld.sock /tmp/mysql.sock 2>/dev/null || true
    
    # Create systemd service for socket symlink persistence
    echo "Setting up socket symlink persistence..."
    cat > /etc/systemd/system/mysql-socket-fix.service << 'EOF'
[Unit]
Description=Fix MySQL socket path for client applications
After=mysql.service
Requires=mysql.service

[Service]
Type=oneshot
ExecStart=/bin/ln -sf /var/run/mysqld/mysqld.sock /tmp/mysql.sock
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable mysql-socket-fix.service >/dev/null 2>&1 || true
    systemctl start mysql-socket-fix.service >/dev/null 2>&1 || true
    
    # Restart MySQL to apply configuration changes
    echo "Restarting MySQL to apply configuration..."
    systemctl restart "$(get_service_name)"
    sleep 3
    
    echo "MySQL client compatibility configuration completed."
}

################################################################################
# SERVICE MANAGEMENT
################################################################################

action_is_installed() {
    local packages
    packages=$(get_packages)
    
    case "$OS_TYPE" in
        fedora)
            for pkg in $packages; do
                if ! rpm -q "$pkg" >/dev/null 2>&1; then
                    echo "false"
                    return 0
                fi
            done
            echo "true"
            ;;
        debian)
            for pkg in $packages; do
                if ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii\|^iU\|^iF\|^iH"; then
                    echo "false"
                    return 0
                fi
            done
            echo "true"
            ;;
        arch)
            for pkg in $packages; do
                if ! pacman -Q "$pkg" >/dev/null 2>&1; then
                    echo "false"
                    return 0
                fi
            done
            echo "true"
            ;;
        *)
            echo "false"
            ;;
    esac
}

action_is_running() {
    local service_name
    service_name=$(get_service_name)
    
    if systemctl is-active --quiet "$service_name"; then
        echo "true"
    else
        echo "false"
    fi
}

action_install() {
    local packages
    packages=$(get_packages)
    
    if [ -z "$packages" ]; then
        echo "ERROR: No packages defined for OS type: $OS_TYPE"
        exit 1
    fi
    
    echo "Installing MySQL packages: $packages"
    install_packages "$packages"
    
    # Initialize MySQL data directory if needed
    local data_dir
    data_dir=$(get_data_dir)
    
    case "$OS_TYPE" in
        fedora|arch)
            if [ ! -d "$data_dir/mysql" ]; then
                echo "Initializing MySQL data directory..."
                mysqld --initialize-insecure --user=mysql --datadir="$data_dir"
            fi
            ;;
        debian)
            # Debian automatically initializes during install
            ;;
    esac
    
    # Start MySQL service
    echo "Starting MySQL service..."
    systemctl start "$(get_service_name)" || true
    systemctl enable "$(get_service_name)" || true
    sleep 3
    
    # Configure MySQL for client compatibility
    echo "Configuring MySQL for client application compatibility..."
    configure_mysql_for_clients
    
    echo "MySQL installation completed successfully!"
    echo ""
    echo "IMPORTANT: For external client applications (Navicat, DBGate, etc.):"
    echo "  - Host: localhost"
    echo "  - Port: 3306" 
    echo "  - Username: root"
    echo "  - Password: (set using: sudo $0 reset-root-password <password>)"
}

action_uninstall() {
    local packages
    packages=$(get_packages)
    
    if [ -z "$packages" ]; then
        echo "ERROR: No packages defined for OS type: $OS_TYPE"
        exit 1
    fi
    
    # Stop service first
    action_stop >/dev/null 2>&1 || true
    
    echo "Uninstalling MySQL packages: $packages"
    uninstall_packages "$packages"
    
    echo "MySQL uninstallation completed"
}

action_start() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl start "$service_name"
    echo "MySQL service started"
}

action_stop() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl stop "$service_name"
    echo "MySQL service stopped"
}

action_restart() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl restart "$service_name"
    echo "MySQL service restarted"
}

action_reload() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl reload "$service_name"
    echo "MySQL service configuration reloaded"
}

action_enable() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl enable "$service_name"
    echo "MySQL service enabled for autostart"
}

action_disable() {
    local service_name
    service_name=$(get_service_name)
    
    systemctl disable "$service_name"
    echo "MySQL service disabled from autostart"
}

################################################################################
# DATABASE MANAGEMENT
################################################################################

# Get MySQL root credentials for commands
get_mysql_auth() {
    local password="$1"
    local socket_path=$(get_socket_path)
    
    if [ -n "$password" ]; then
        echo "-p$password --socket=$socket_path"
    else
        # Try without password first
        if mysql -u root --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "--socket=$socket_path"
        else
            echo "ERROR: MySQL root password required but not provided"
            exit 1
        fi
    fi
}

action_database_list() {
    local json_output=false
    local root_password=""
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --json)
                json_output=true
                shift
                ;;
            --root-password)
                root_password="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    local socket_path=$(get_socket_path)
    local output
    
    # Try different authentication methods
    if [ -n "$root_password" ]; then
        # Try with password first
        if ! output=$(mysql -u root -p"$root_password" --socket="$socket_path" -e "SHOW DATABASES;" -s -N 2>/dev/null); then
            # Fallback to sudo
            output=$(sudo mysql -u root --socket="$socket_path" -e "SHOW DATABASES;" -s -N 2>/dev/null)
        fi
    else
        # Try without password first
        if ! output=$(mysql -u root --socket="$socket_path" -e "SHOW DATABASES;" -s -N 2>/dev/null); then
            # Fallback to sudo
            output=$(sudo mysql -u root --socket="$socket_path" -e "SHOW DATABASES;" -s -N 2>/dev/null)
        fi
    fi
    
    # Filter system databases
    local filtered_output
    filtered_output=$(echo "$output" | grep -v "information_schema\|performance_schema\|mysql\|sys")
    
    if [ "$json_output" = true ]; then
        {
            echo "["
            echo "$filtered_output" | \
            sed 's/.*/"&"/' | \
            sed '$!s/$/,/'
            echo "]"
        } | tr -d '\n' | sed 's/,]/]/'
    else
        echo "$filtered_output"
    fi
}

action_database_create() {
    local database_name="$1"
    local root_password="$2"
    
    if [ -z "$database_name" ]; then
        echo "ERROR: Database name is required"
        exit 1
    fi
    
    local socket_path=$(get_socket_path)
    
    # Try different authentication methods
    local success=false
    local sql="CREATE DATABASE IF NOT EXISTS \`$database_name\`;"
    
    # Method 1: Try with root password if provided
    if [ -n "$root_password" ] && [ "$success" = false ]; then
        if mysql -u root -p"$root_password" --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 2: Try without password (socket auth)
    if [ "$success" = false ]; then
        if mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 3: Try with sudo (socket auth)
    if [ "$success" = false ]; then
        if sudo mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    if [ "$success" = true ]; then
        echo "Database '$database_name' created successfully"
    else
        echo "ERROR: Failed to create database '$database_name'. Please check MySQL authentication."
        exit 1
    fi
}

action_database_drop() {
    local database_name="$1"
    local root_password="$2"
    
    if [ -z "$database_name" ]; then
        echo "ERROR: Database name is required"
        exit 1
    fi
    
    local socket_path=$(get_socket_path)
    
    # Try different authentication methods
    local success=false
    local sql="DROP DATABASE IF EXISTS \`$database_name\`;"
    
    # Method 1: Try with root password if provided
    if [ -n "$root_password" ] && [ "$success" = false ]; then
        if mysql -u root -p"$root_password" --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 2: Try without password (socket auth)
    if [ "$success" = false ]; then
        if mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 3: Try with sudo (socket auth)  
    if [ "$success" = false ]; then
        if sudo mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    if [ "$success" = true ]; then
        echo "Database '$database_name' dropped successfully"
    else
        echo "ERROR: Failed to drop database '$database_name'. Please check MySQL authentication."
        exit 1
    fi
}

################################################################################
# USER MANAGEMENT
################################################################################

action_user_create() {
    local username="$1"
    local password="$2"
    local host="${3:-localhost}"
    local root_password="$4"
    
    if [ -z "$username" ] || [ -z "$password" ]; then
        echo "ERROR: Username and password are required"
        exit 1
    fi
    
    local socket_path=$(get_socket_path)
    
    # Try different authentication methods
    local success=false
    local sql="CREATE USER IF NOT EXISTS '$username'@'$host' IDENTIFIED BY '$password';"
    
    # Method 1: Try with root password if provided
    if [ -n "$root_password" ] && [ "$success" = false ]; then
        if mysql -u root -p"$root_password" --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 2: Try without password (socket auth)
    if [ "$success" = false ]; then
        if mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    # Method 3: Try with sudo (socket auth)
    if [ "$success" = false ]; then
        if sudo mysql -u root --socket="$socket_path" -e "$sql" 2>/dev/null; then
            success=true
        fi
    fi
    
    if [ "$success" = true ]; then
        echo "User '$username'@'$host' created successfully"
    else
        echo "ERROR: Failed to create user '$username'@'$host'. Please check MySQL authentication."
        exit 1
    fi
}

action_grant_privileges() {
    local username="$1"
    local database="${2:-*}"
    local privileges="${3:-ALL}"
    local host="${4:-localhost}"
    local root_password="$5"
    
    if [ -z "$username" ]; then
        echo "ERROR: Username is required"
        exit 1
    fi
    
    local socket_path=$(get_socket_path)
    local auth_params
    if [ -n "$root_password" ]; then
        auth_params="-p$root_password --socket=$socket_path"
    else
        auth_params="--socket=$socket_path"
    fi
    
    local db_spec
    if [ "$database" = "*" ]; then
        db_spec="*.*"
    else
        db_spec="\`$database\`.*"
    fi
    
    mysql -u root $auth_params -e "GRANT $privileges ON $db_spec TO '$username'@'$host';" 2>/dev/null
    mysql -u root $auth_params -e "FLUSH PRIVILEGES;" 2>/dev/null
    echo "Privileges '$privileges' on '$database' granted to '$username'@'$host'"
}

################################################################################
# PASSWORD MANAGEMENT
################################################################################

action_check_root_password() {
    local password="$1"
    local socket_path=$(get_socket_path)
    
    if [ -n "$password" ]; then
        if mysql -u root -p"$password" --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "true"
        else
            echo "false"
        fi
    else
        # Try without password first
        if mysql -u root --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "true"
        # Try with sudo (Ubuntu/Debian socket auth)
        elif sudo mysql -u root --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "true"
        else
            echo "false"
        fi
    fi
}

action_set_root_password() {
    local new_password="$1"
    
    if [ -z "$new_password" ]; then
        echo "ERROR: New password is required"
        exit 1
    fi
    
    echo "Resetting MySQL root password (this will temporarily stop MySQL)..."
    
    # Get service name for current OS
    local service_name=$(get_service_name)
    
    # Stop MySQL service
    echo "Stopping MySQL service..."
    systemctl stop "$service_name" 2>/dev/null || service "$service_name" stop 2>/dev/null || true
    sleep 2
    
    # Create temporary init file for password reset
    local temp_init_file="/tmp/mysql_init_$$.sql"
    cat > "$temp_init_file" << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$new_password';
FLUSH PRIVILEGES;
EOF
    
    # Start MySQL with skip-grant-tables and init-file
    echo "Starting MySQL in safe mode to reset password..."
    
    case "$OS_TYPE" in
        debian)
            # For Ubuntu/Debian
            mysqld_safe --skip-grant-tables --init-file="$temp_init_file" &
            ;;
        fedora)
            # For Fedora/RHEL
            mysqld --skip-grant-tables --init-file="$temp_init_file" &
            ;;
        arch)
            # For Arch
            mysqld --skip-grant-tables --init-file="$temp_init_file" &
            ;;
    esac
    
    local mysqld_pid=$!
    sleep 5
    
    # Kill the temporary mysqld process
    kill $mysqld_pid 2>/dev/null || true
    sleep 2
    
    # Clean up temp file
    rm -f "$temp_init_file"
    
    # Start MySQL service normally
    echo "Restarting MySQL service..."
    systemctl start "$service_name" 2>/dev/null || service "$service_name" start 2>/dev/null
    sleep 3
    
    # Verify password was set
    local socket_path=$(get_socket_path)
    if mysql -u root -p"$new_password" --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
        echo "Root password reset successfully"
        echo "New password is active and working"
    else
        echo "WARNING: Password may have been set, but verification failed"
        echo "Please try logging in with: mysql -u root -p --socket=$socket_path"
    fi
}

action_reset_root_password() {
    local new_password="$1"
    
    if [ -z "$new_password" ]; then
        echo "ERROR: New password is required"
        exit 1
    fi
    
    echo "🔄 Resetting MySQL root password..."
    
    local service_name=$(get_service_name)
    local success=false
    
    # Method 1: Try using debian-sys-maint user (Debian/Ubuntu specific)
    if [ -f /etc/mysql/debian.cnf ] && [ "$OS_TYPE" = "debian" ]; then
        echo "🔑 Using debian-sys-maint credentials..."
        
        # Try to connect with debian-sys-maint and change root password
        if sudo mysql --defaults-file=/etc/mysql/debian.cnf -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$new_password'; FLUSH PRIVILEGES;" 2>/dev/null; then
            success=true
            echo "✅ Root password changed using debian-sys-maint"
        fi
    fi
    
    # If debian method worked, verify and exit
    if [ "$success" = true ]; then
        local socket_path=$(get_socket_path)
        
        # Enable TCP authentication for client applications
        echo "🔧 Enabling TCP authentication for client applications..."
        if sudo mysql -u root --socket="$socket_path" -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$new_password'; FLUSH PRIVILEGES;" 2>/dev/null; then
            echo "✅ TCP authentication enabled successfully"
        fi
        
        if mysql -u root -p"$new_password" --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "✅ MySQL root password reset successfully!"
            echo ""
            echo "CONNECTION INFORMATION:"
            echo "  TCP Connection (for Navicat, DBGate, etc.):"
            echo "    Host: localhost"
            echo "    Port: 3306"
            echo "    Username: root"
            echo "    Password: $new_password"
            echo ""
            echo "  Socket Connection:"
            echo "    Socket: $socket_path"
            echo "    Command: mysql -u root -p --socket=$socket_path"
            return 0
        else
            echo "⚠️  Password was set but MySQL service may not be running properly"
            echo "   Try restarting MySQL: sudo systemctl restart mysql"
            echo "   Then test: mysql -u root -p --socket=$socket_path"
        fi
    fi
    
    # Stop MySQL service completely
    echo "⏹️  Stopping MySQL service..."
    systemctl stop "$service_name" 2>/dev/null || true
    sleep 3
    
    # Force kill any remaining MySQL processes
    echo "🔪 Terminating all MySQL processes..."
    pkill -9 -f mysqld 2>/dev/null || true
    pkill -9 -f mysql 2>/dev/null || true
    sleep 3
    
    # Wait until no MySQL processes are running
    local attempts=0
    while pgrep -f mysqld >/dev/null 2>&1 && [ $attempts -lt 10 ]; do
        echo "   Waiting for MySQL processes to terminate..."
        sleep 1
        attempts=$((attempts + 1))
    done
    
    # Ensure required directories exist
    echo "📁 Setting up MySQL directories..."
    mkdir -p /var/run/mysqld
    chown mysql:mysql /var/run/mysqld
    chmod 755 /var/run/mysqld
    
    # Create temporary init file with proper permissions
    local temp_init="/tmp/mysql_reset_$$.sql"
    cat > "$temp_init" << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$new_password';
FLUSH PRIVILEGES;
EOF
    
    # Set proper permissions for MySQL to read the file
    chmod 644 "$temp_init"
    chown mysql:mysql "$temp_init" 2>/dev/null || true
    
    echo "🔑 Starting MySQL with password reset..."
    
    # Try different methods based on OS
    case "$OS_TYPE" in
        debian|ubuntu)
            # For Debian/Ubuntu systems
            mysqld_safe --skip-grant-tables --init-file="$temp_init" --user=mysql --datadir=/var/lib/mysql &
            ;;
        *)
            # Generic approach
            mysqld --skip-grant-tables --init-file="$temp_init" --user=mysql &
            ;;
    esac
    
    local mysqld_pid=$!
    sleep 8
    
    # Check if password reset worked by connecting
    echo "🧪 Testing new password..."
    local socket_path=$(get_socket_path)
    for i in {1..5}; do
        if mysql -u root -p"$new_password" --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            success=true
            break
        fi
        sleep 2
    done
    
    # Stop the temporary MySQL process
    kill $mysqld_pid 2>/dev/null || true
    pkill -f mysqld 2>/dev/null || true
    sleep 3
    
    # Clean up temp file
    rm -f "$temp_init"
    
    # Restart MySQL service normally
    echo "� Restarting MySQL service..."
    systemctl start "$service_name" 2>/dev/null
    sleep 5
    
    # Final verification
    if [ "$success" = true ]; then
        local socket_path=$(get_socket_path)
        if mysql -u root -p"$new_password" --socket="$socket_path" -e "SELECT 1;" >/dev/null 2>&1; then
            echo "✅ MySQL root password reset successfully!"
            
            # Enable TCP authentication for client applications
            echo "🔧 Enabling TCP authentication for client applications..."
            if sudo mysql -u root --socket="$socket_path" -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$new_password'; FLUSH PRIVILEGES;" 2>/dev/null; then
                echo "✅ TCP authentication enabled successfully"
                echo ""
                echo "CONNECTION INFORMATION:"
                echo "  TCP Connection (for Navicat, DBGate, etc.):"
                echo "    Host: localhost"
                echo "    Port: 3306"
                echo "    Username: root"
                echo "    Password: $new_password"
                echo ""
                echo "  Socket Connection:"
                echo "    Socket: $socket_path"
                echo "    Command: mysql -u root -p --socket=$socket_path"
            else
                echo "⚠️  Password reset but TCP authentication setup failed"
                echo "   Socket connection: mysql -u root -p --socket=$socket_path"
            fi
        else
            echo "⚠️  Password reset but verification failed after restart"
            echo "   Please try: mysql -u root -p --socket=$socket_path"
        fi
    else
        # Try alternative method using direct file manipulation
        echo "🔄 Trying alternative method..."
        systemctl stop "$service_name" 2>/dev/null
        
        # Direct MySQL socket connection
        mysqld_safe --skip-grant-tables --skip-networking &
        local safe_pid=$!
        sleep 5
        
        # Try to connect and change password
        local socket_path=$(get_socket_path)
        if mysql -u root --socket="$socket_path" -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$new_password'; FLUSH PRIVILEGES;" 2>/dev/null; then
            echo "✅ Password reset with alternative method"
            success=true
        fi
        
        kill $safe_pid 2>/dev/null
        systemctl start "$service_name" 2>/dev/null
        sleep 3
        
        if [ "$success" = false ]; then
            local socket_path=$(get_socket_path)
            echo "❌ All automatic methods failed. Manual reset required:"
            echo "   1. sudo systemctl stop mysql"
            echo "   2. sudo mysqld_safe --skip-grant-tables --skip-networking &"
            echo "   3. mysql -u root --socket=$socket_path"
            echo "   4. ALTER USER 'root'@'localhost' IDENTIFIED BY '$new_password';"
            echo "   5. FLUSH PRIVILEGES;"
            echo "   6. exit"
            echo "   7. sudo pkill mysqld && sudo systemctl start mysql"
            exit 1
        fi
    fi
}

action_secure_installation() {
    echo "Please run 'mysql_secure_installation' manually for interactive setup"
    echo "This script provides automated alternatives:"
    echo "  - Use 'set-root-password <password>' to set root password"
    echo "  - Use 'database-drop test' to remove test database"
    echo "  - Use MySQL configuration to disable remote root login"
}

################################################################################
# STATUS & INFO
################################################################################

action_status_info() {
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
    
    local is_installed
    local is_running
    local version=""
    local data_dir
    local config_dir
    local socket_path
    
    is_installed=$(action_is_installed)
    is_running=$(action_is_running)
    data_dir=$(get_data_dir)
    config_dir=$(get_config_dir)
    socket_path=$(get_socket_path)
    
    if [ "$is_installed" = "true" ]; then
        version=$(mysql --version 2>/dev/null | grep -o 'Ver [0-9]*\.[0-9]*\.[0-9]*' | awk '{print $2}' || echo "unknown")
    fi
    
    if [ "$json_output" = true ]; then
        cat <<EOF
{
    "installed": $is_installed,
    "running": $is_running,
    "version": "$version",
    "data_directory": "$data_dir",
    "config_directory": "$config_dir",
    "socket_path": "$socket_path",
    "default_port": 3306
}
EOF
    else
        echo "MySQL Status:"
        echo "  Installed: $is_installed"
        echo "  Running: $is_running"
        echo "  Version: $version"
        echo "  Data Directory: $data_dir"
        echo "  Config Directory: $config_dir"
        echo "  Socket Path: $socket_path"
        echo "  Default Port: 3306"
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
        # Service management
        is-installed)           action_is_installed ;;
        is-running)             action_is_running ;;
        install)                action_install ;;
        uninstall)              action_uninstall ;;
        start)                  action_start ;;
        stop)                   action_stop ;;
        restart)                action_restart ;;
        reload)                 action_reload ;;
        enable)                 action_enable ;;
        disable)                action_disable ;;
        
        # Database management
        database-list)          action_database_list "$@" ;;
        database-create)        action_database_create "$@" ;;
        database-drop)          action_database_drop "$@" ;;
        
        # User management
        user-create)            action_user_create "$@" ;;
        grant-privileges)       action_grant_privileges "$@" ;;
        
        # Password management
        check-root-password)    action_check_root_password "$@" ;;
        set-root-password)      action_set_root_password "$@" ;;
        reset-root-password)    action_reset_root_password "$@" ;;
        secure-installation)    action_secure_installation ;;
        
        # Client Configuration
        setup-for-clients)      configure_mysql_for_clients ;;
        
        # Status & Info
        status-info)            action_status_info "$@" ;;
        
        # Help
        --help|help)
            cat <<EOF
MySQL Database Server Management Script

USAGE: mysql.sh <action> [args...]

SERVICE MANAGEMENT:
  is-installed                              Check if MySQL is installed
  is-running                                Check if MySQL is running
  install                                   Install MySQL server
  uninstall                                 Uninstall MySQL server
  start                                     Start MySQL service
  stop                                      Stop MySQL service
  restart                                   Restart MySQL service
  reload                                    Reload MySQL configuration
  enable                                    Enable MySQL autostart
  disable                                   Disable MySQL autostart

DATABASE MANAGEMENT:
  database-list [--json] [--root-password <pass>]     List all databases
  database-create <name> [<root_password>]            Create new database
  database-drop <name> [<root_password>]              Drop database

USER MANAGEMENT:
  user-create <username> <password> [<host>] [<root_password>]
                                            Create MySQL user
  grant-privileges <username> [<database>] [<privileges>] [<host>] [<root_password>]
                                            Grant privileges to user

PASSWORD MANAGEMENT:
  check-root-password [<password>]          Check if root password is correct
  set-root-password <new_password> [<current_password>]
                                            Set MySQL root password (if you know current)
  reset-root-password <new_password>        Reset MySQL root password (no current password needed)
  secure-installation                       Show secure installation info

CLIENT CONFIGURATION:
  setup-for-clients                         Configure MySQL for external client applications

STATUS & INFO:
  status-info [--json]                      Show MySQL status information

EXAMPLES:
  # Install MySQL
  sudo ./mysql.sh install
  
  # Set root password (if you know current password)
  sudo ./mysql.sh set-root-password "newpassword"
  
  # Reset root password (mevcut şifreyi bilmeden)
  sudo ./mysql.sh reset-root-password "newpassword"
  
  # Create database
  sudo ./mysql.sh database-create myapp mypassword
  
  # Create user with privileges
  sudo ./mysql.sh user-create myuser mypass localhost rootpass
  sudo ./mysql.sh grant-privileges myuser myapp ALL localhost rootpass
  
  # List databases
  ./mysql.sh database-list --json --root-password mypass

EOF
            exit 0
            ;;
        
        *)
            echo "ERROR: Unknown action: $action"
            echo "Use 'mysql.sh --help' for usage information"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
