#!/bin/bash
#
# Hosts File Management Script
# Manages /etc/hosts file entries for local domain mapping
#
# Usage: hosts.sh <action> [arguments]
#
# Actions:
#   list [--json]              List all custom hosts entries
#   add <ip> <domain>          Add new hosts entry
#   remove <domain>            Remove hosts entry by domain
#   exists <domain>            Check if domain exists
#   backup                     Backup hosts file
#   restore                    Restore hosts file from backup
#   validate <ip>              Validate IP address format
#
# Exit codes:
#   0 = Success
#   1 = General error
#   2 = Invalid arguments
#   3 = File permission error

set -e

# ============================================
# OS DETECTION (First 20 lines)
# ============================================

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="$ID"
    OS_ID_LIKE="$ID_LIKE"
else
    echo "Error: Cannot detect OS type" >&2
    exit 1
fi

# Detect OS type
if [[ "$OS_ID" == "fedora" ]] || [[ "$OS_ID_LIKE" == *"fedora"* ]]; then
    OS_TYPE="fedora"
elif [[ "$OS_ID" == "ubuntu" ]] || [[ "$OS_ID_LIKE" == *"ubuntu"* ]]; then
    OS_TYPE="ubuntu"
elif [[ "$OS_ID" == "debian" ]] || [[ "$OS_ID_LIKE" == *"debian"* ]]; then
    OS_TYPE="debian"
elif [[ "$OS_ID" == "arch" ]] || [[ "$OS_ID_LIKE" == *"arch"* ]] || [[ "$OS_ID" == "manjaro" ]]; then
    OS_TYPE="arch"
else
    OS_TYPE="unknown"
    echo "Warning: Unsupported OS: $OS_ID" >&2
fi

# ============================================
# CONSTANTS
# ============================================

HOSTS_FILE="/etc/hosts"
BACKUP_DIR="/var/backups/orkesta"
BACKUP_FILE="$BACKUP_DIR/hosts.backup"
MARKER_START="# Orkesta Managed Entries - START"
MARKER_END="# Orkesta Managed Entries - END"

# ============================================
# HELPER FUNCTIONS
# ============================================

# Validate IP address format
validate_ip() {
    local ip="$1"
    
    # IPv4 validation regex
    if [[ $ip =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        # Check each octet is 0-255
        IFS='.' read -ra OCTETS <<< "$ip"
        for octet in "${OCTETS[@]}"; do
            if ((octet > 255)); then
                return 1
            fi
        done
        return 0
    fi
    
    # IPv6 validation (basic)
    if [[ $ip =~ ^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$ ]]; then
        return 0
    fi
    
    return 1
}

# Validate domain name
validate_domain() {
    local domain="$1"
    
    # Basic domain validation
    if [[ $domain =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        return 0
    fi
    
    return 1
}

# Check if hosts file has Orkesta section
has_orkesta_section() {
    grep -q "$MARKER_START" "$HOSTS_FILE" 2>/dev/null
}

# Initialize Orkesta section if not exists
init_orkesta_section() {
    if ! has_orkesta_section; then
        echo "" >> "$HOSTS_FILE"
        echo "$MARKER_START" >> "$HOSTS_FILE"
        echo "$MARKER_END" >> "$HOSTS_FILE"
    fi
}

# Get Orkesta managed entries (between markers)
get_managed_entries() {
    if ! has_orkesta_section; then
        return
    fi
    
    sed -n "/$MARKER_START/,/$MARKER_END/p" "$HOSTS_FILE" | \
        grep -v "^#" | \
        grep -v "^$" | \
        awk '{print $1 " " $2}'
}

# ============================================
# ACTIONS
# ============================================

action_list() {
    local format="${1:-text}"
    
    if [[ "$format" == "--json" ]]; then
        # JSON output - TÜM hosts dosyasını göster
        echo "["
        local first=true
        
        # Tüm hosts dosyasını oku (yorumlar ve boş satırlar hariç)
        while IFS= read -r line; do
            # Boş satırları ve yorum satırlarını atla
            if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
                continue
            fi
            
            # IP ve domain'i ayır
            local ip=$(echo "$line" | awk '{print $1}')
            local domain=$(echo "$line" | awk '{print $2}')
            
            # IP ve domain geçerliyse ekle
            if [[ -n "$ip" ]] && [[ -n "$domain" ]]; then
                if [[ "$first" == true ]]; then
                    first=false
                else
                    echo ","
                fi
                
                # Orkesta tarafından yönetilip yönetilmediğini kontrol et
                local managed="false"
                if has_orkesta_section; then
                    if get_managed_entries | grep -q "^$ip[[:space:]]$domain$"; then
                        managed="true"
                    fi
                fi
                
                echo -n "  {\"ip\": \"$ip\", \"domain\": \"$domain\", \"managed\": $managed}"
            fi
        done < "$HOSTS_FILE"
        
        echo ""
        echo "]"
    else
        # Text output - TÜM hosts dosyası
        grep -v "^#" "$HOSTS_FILE" | grep -v "^$" | awk '{print $1 " " $2}'
    fi
}

action_add() {
    local ip="$1"
    local domain="$2"
    
    if [[ -z "$ip" ]] || [[ -z "$domain" ]]; then
        echo "Error: IP and domain are required" >&2
        exit 2
    fi
    
    # Validate IP
    if ! validate_ip "$ip"; then
        echo "Error: Invalid IP address: $ip" >&2
        exit 2
    fi
    
    # Validate domain
    if ! validate_domain "$domain"; then
        echo "Error: Invalid domain name: $domain" >&2
        exit 2
    fi
    
    # Check if domain already exists
    if grep -q "[[:space:]]$domain[[:space:]]*$" "$HOSTS_FILE" 2>/dev/null; then
        echo "Error: Domain '$domain' already exists in hosts file" >&2
        exit 1
    fi
    
    # Initialize section if needed
    init_orkesta_section
    
    # Add entry before the END marker
    local temp_file=$(mktemp)
    awk -v ip="$ip" -v domain="$domain" -v marker="$MARKER_END" '
        $0 ~ marker { print ip "\t" domain }
        { print }
    ' "$HOSTS_FILE" > "$temp_file"
    
    # Replace hosts file
    if ! mv "$temp_file" "$HOSTS_FILE"; then
        echo "Error: Failed to update hosts file" >&2
        rm -f "$temp_file"
        exit 3
    fi
    
    echo "Successfully added: $ip → $domain"
}

action_remove() {
    local domain="$1"
    
    if [[ -z "$domain" ]]; then
        echo "Error: Domain is required" >&2
        exit 2
    fi
    
    # Check if domain exists
    if ! grep -q "[[:space:]]$domain[[:space:]]*$" "$HOSTS_FILE" 2>/dev/null; then
        echo "Error: Domain '$domain' not found in hosts file" >&2
        exit 1
    fi
    
    # Remove entry
    local temp_file=$(mktemp)
    grep -v "[[:space:]]$domain[[:space:]]*$" "$HOSTS_FILE" > "$temp_file"
    
    if ! mv "$temp_file" "$HOSTS_FILE"; then
        echo "Error: Failed to update hosts file" >&2
        rm -f "$temp_file"
        exit 3
    fi
    
    echo "Successfully removed: $domain"
}

action_exists() {
    local domain="$1"
    
    if [[ -z "$domain" ]]; then
        echo "Error: Domain is required" >&2
        exit 2
    fi
    
    if grep -q "[[:space:]]$domain[[:space:]]*$" "$HOSTS_FILE" 2>/dev/null; then
        echo "true"
        exit 0
    else
        echo "false"
        exit 0
    fi
}

action_backup() {
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup hosts file
    if ! cp "$HOSTS_FILE" "$BACKUP_FILE"; then
        echo "Error: Failed to backup hosts file" >&2
        exit 3
    fi
    
    echo "Hosts file backed up to: $BACKUP_FILE"
}

action_restore() {
    # Check if backup exists
    if [[ ! -f "$BACKUP_FILE" ]]; then
        echo "Error: Backup file not found: $BACKUP_FILE" >&2
        exit 1
    fi
    
    # Restore backup
    if ! cp "$BACKUP_FILE" "$HOSTS_FILE"; then
        echo "Error: Failed to restore hosts file" >&2
        exit 3
    fi
    
    echo "Hosts file restored from: $BACKUP_FILE"
}

action_validate_ip() {
    local ip="$1"
    
    if [[ -z "$ip" ]]; then
        echo "Error: IP is required" >&2
        exit 2
    fi
    
    if validate_ip "$ip"; then
        echo "true"
        exit 0
    else
        echo "false"
        exit 0
    fi
}

# ============================================
# MAIN
# ============================================

# Check if hosts file exists
if [[ ! -f "$HOSTS_FILE" ]]; then
    echo "Error: Hosts file not found: $HOSTS_FILE" >&2
    exit 1
fi

# Parse action
ACTION="${1:-}"

if [[ -z "$ACTION" ]]; then
    echo "Error: Action is required" >&2
    echo "Usage: $0 <action> [arguments]" >&2
    exit 2
fi

case "$ACTION" in
    list)
        action_list "$2"
        ;;
    add)
        action_add "$2" "$3"
        ;;
    remove)
        action_remove "$2"
        ;;
    exists)
        action_exists "$2"
        ;;
    backup)
        action_backup
        ;;
    restore)
        action_restore
        ;;
    validate)
        action_validate_ip "$2"
        ;;
    *)
        echo "Error: Unknown action: $ACTION" >&2
        exit 2
        ;;
esac

exit 0
