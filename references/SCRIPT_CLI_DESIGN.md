# Orkesta Script CLI Design

**Date**: 9 Kasım 2025  
**Purpose**: CLI-First script design principles and standards

---

## 🎯 Core Principle

> **Every script is a standalone CLI tool** - like VestaCP, cPanel, or aaPanel commands

```bash
# ✅ Script works independently
sudo scripts/apache/vhost-create.sh example.com /var/www/html --ssl

# ✅ GUI just calls the script
python: subprocess.run(['pkexec', script_path, *args])

# ❌ Script NOT dependent on Python/GTK
# Script içinde GTK/Python kodu olmamalı!
```

---

## 📋 Script Standards Checklist

Every script MUST have:

- [ ] **Shebang**: `#!/bin/bash`
- [ ] **Error handling**: `set -e` (exit on error)
- [ ] **Help function**: `--help` flag with full documentation
- [ ] **Parameter parsing**: Argument handling with validation
- [ ] **OS detection**: Multi-distro support (Fedora/Debian/Arch)
- [ ] **Exit codes**: 0=success, 1=error, 2=invalid params, 3=permission denied
- [ ] **Output formats**: Human-readable (default) + JSON (--json flag)
- [ ] **Dry-run mode**: `--dry-run` flag for testing
- [ ] **Verbose mode**: `--verbose` flag for debugging
- [ ] **Idempotent**: Can run multiple times safely
- [ ] **Error messages**: stderr for errors, stdout for output
- [ ] **No hardcoding**: All paths/values from parameters or OS detection

---

## 🛠️ Script Template

```bash
#!/bin/bash
# scripts/SERVICE/ACTION.sh
# Brief description of what this script does
#
# Usage: ACTION.sh <required_param> [options]
# Exit codes: 0=success, 1=error, 2=invalid params, 3=permission denied

set -e  # Exit on any error

# ============================================
# CONFIGURATION
# ============================================
SCRIPT_NAME=$(basename "$0")
SCRIPT_VERSION="1.0"

# ============================================
# HELP FUNCTION
# ============================================
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME <required_param> [options]

Brief description of what this script does.

Arguments:
  param1          Description of required parameter
  param2          Description of another parameter

Options:
  --option1       Description of option
  --option2=VAL   Description of option with value
  --json          Output result as JSON
  --dry-run       Show what would be done without executing
  --verbose       Verbose output for debugging
  --help          Show this help message

Examples:
  # Basic usage
  $SCRIPT_NAME value1 value2

  # With options
  $SCRIPT_NAME value1 value2 --option1 --option2=something

  # Dry run mode
  $SCRIPT_NAME value1 value2 --dry-run

  # JSON output for automation
  $SCRIPT_NAME value1 value2 --json

Exit Codes:
  0 - Success
  1 - General error
  2 - Invalid parameters
  3 - Permission denied
  4 - Service not available

Author: Orkesta Team
Version: $SCRIPT_VERSION
EOF
    exit 0
}

# ============================================
# PARAMETER PARSING
# ============================================
PARAM1=""
PARAM2=""
OPTION1=false
OPTION2=""
JSON_OUTPUT=false
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --option1)
            OPTION1=true
            shift
            ;;
        --option2=*)
            OPTION2="${1#*=}"
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            # Positional parameters
            if [ -z "$PARAM1" ]; then
                PARAM1="$1"
            elif [ -z "$PARAM2" ]; then
                PARAM2="$1"
            else
                echo "Error: Unknown parameter: $1" >&2
                echo "Run with --help for usage information" >&2
                exit 2
            fi
            shift
            ;;
    esac
done

# ============================================
# VALIDATION
# ============================================
if [ -z "$PARAM1" ]; then
    echo "Error: Required parameter missing" >&2
    echo "Run with --help for usage information" >&2
    exit 2
fi

# Additional validation
# ...

# ============================================
# OS DETECTION
# ============================================
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

OS_TYPE=$(detect_os)

if [ "$OS_TYPE" = "unknown" ]; then
    echo "Error: Cannot detect operating system" >&2
    exit 4
fi

[ "$VERBOSE" = true ] && echo "Detected OS: $OS_TYPE"

# ============================================
# OS-SPECIFIC CONFIGURATION
# ============================================
case $OS_TYPE in
    fedora)
        # Fedora-specific paths/commands
        SERVICE_NAME="httpd"
        CONFIG_DIR="/etc/httpd"
        [ "$VERBOSE" = true ] && echo "Using Fedora configuration"
        ;;
    ubuntu|debian)
        # Debian/Ubuntu-specific paths/commands
        SERVICE_NAME="apache2"
        CONFIG_DIR="/etc/apache2"
        [ "$VERBOSE" = true ] && echo "Using Debian/Ubuntu configuration"
        ;;
    arch)
        # Arch-specific paths/commands
        SERVICE_NAME="httpd"
        CONFIG_DIR="/etc/httpd"
        [ "$VERBOSE" = true ] && echo "Using Arch configuration"
        ;;
    *)
        echo "Error: Unsupported OS: $OS_TYPE" >&2
        exit 4
        ;;
esac

# ============================================
# DRY RUN MODE
# ============================================
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN MODE - No changes will be made"
    echo ""
    echo "Would execute:"
    echo "  Parameter 1: $PARAM1"
    echo "  Parameter 2: $PARAM2"
    [ "$OPTION1" = true ] && echo "  Option 1: Enabled"
    [ -n "$OPTION2" ] && echo "  Option 2: $OPTION2"
    exit 0
fi

# ============================================
# MAIN LOGIC
# ============================================
[ "$VERBOSE" = true ] && echo "Starting main operation..."

# Check permissions if needed
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root" >&2
    echo "Please use: sudo $SCRIPT_NAME" >&2
    exit 3
fi

# Main operations here
# ...

[ "$VERBOSE" = true ] && echo "Operation completed successfully"

# ============================================
# OUTPUT
# ============================================
if [ "$JSON_OUTPUT" = true ]; then
    # JSON output for automation
    cat << EOF
{
  "success": true,
  "param1": "$PARAM1",
  "param2": "$PARAM2",
  "os_type": "$OS_TYPE"
}
EOF
else
    # Human-readable output
    echo "✅ Operation completed successfully"
    echo "   Parameter 1: $PARAM1"
    echo "   Parameter 2: $PARAM2"
fi

exit 0
```

---

## 📊 Script Comparison Table

| Feature | ✅ Good Script | ❌ Bad Script |
|---------|---------------|---------------|
| **Independence** | Runs standalone | Requires Python/GTK |
| **Help** | Built-in `--help` | No documentation |
| **Parameters** | Flexible args | Hardcoded values |
| **Exit Codes** | Standard (0=success) | No exit codes |
| **OS Support** | Multi-distro | Single distro |
| **Output** | Human + JSON | Only prints |
| **Testing** | Has `--dry-run` | No test mode |
| **Errors** | Clear messages | Silent fails |
| **Usage** | CLI + GUI + Automation | GUI only |

---

## 🎯 Real-World Examples

### VestaCP Style
```bash
# VestaCP commands
v-add-web-domain admin example.com
v-add-database admin db_name db_user
v-list-web-domains admin

# Orkesta equivalent
orkesta-apache vhost-create example.com /var/www/html
orkesta-mysql database-create db_name --user=db_user
orkesta-apache vhost-list
```

### cPanel Style
```bash
# cPanel (uapi)
uapi DomainInfo domains_data domain=example.com
uapi Mysql create_database name=mydb

# Orkesta equivalent
scripts/apache/vhost-list.sh --json | jq '.[] | select(.domain=="example.com")'
scripts/mysql/database-create.sh mydb
```

### aaPanel Style
```bash
# aaPanel CLI
bt site add -d example.com -p /var/www/html
bt database add -n mydb -u myuser

# Orkesta equivalent
scripts/apache/vhost-create.sh example.com /var/www/html
scripts/mysql/database-create.sh mydb --user=myuser
```

---

## 🔄 Integration Examples

### From Python (GUI)
```python
import subprocess
import json

def call_script(script, *args, json_output=False):
    """Call Orkesta CLI script"""
    cmd = ['pkexec', script] + list(args)
    if json_output:
        cmd.append('--json')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if json_output:
        return json.loads(result.stdout)
    
    return result.returncode == 0, result.stdout

# Usage
success, output = call_script(
    'scripts/apache/vhost-create.sh',
    'example.com',
    '/var/www/html',
    '--ssl',
    '--php=8.2'
)
```

### From Bash (Automation)
```bash
#!/bin/bash
# deploy_wordpress.sh

DOMAIN=$1

# Create VHost
if scripts/apache/vhost-create.sh "$DOMAIN" "/var/www/$DOMAIN" --ssl --php=8.2; then
    echo "✅ VHost created"
else
    echo "❌ Failed"
    exit 1
fi

# Create DB
DB_NAME="${DOMAIN//./_}_db"
scripts/mysql/database-create.sh "$DB_NAME" --user="${DB_NAME}_user"
```

### From PHP (Web Panel)
```php
<?php
function executeScript($script, $args = []) {
    $cmd = 'sudo ' . escapeshellcmd($script);
    foreach ($args as $arg) {
        $cmd .= ' ' . escapeshellarg($arg);
    }
    $cmd .= ' --json 2>&1';
    
    $output = shell_exec($cmd);
    return json_decode($output, true);
}

$result = executeScript('scripts/apache/vhost-list.sh');
?>
```

---

## 📝 Testing Scripts

### Manual Testing
```bash
# Test help
./script.sh --help

# Test dry-run
./script.sh param1 param2 --dry-run

# Test verbose
./script.sh param1 param2 --verbose

# Test JSON output
./script.sh param1 param2 --json | jq .

# Test invalid params
./script.sh  # Should exit with code 2

# Test without sudo (if required)
./script.sh param1 param2  # Should exit with code 3
```

### Automated Testing
```bash
#!/bin/bash
# test_script.sh

SCRIPT="./scripts/apache/vhost-create.sh"

# Test 1: Help
echo "Test 1: Help"
$SCRIPT --help
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Missing params
echo "Test 2: Missing params"
$SCRIPT 2>/dev/null
[ $? -eq 2 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Dry-run
echo "Test 3: Dry-run"
$SCRIPT example.com /var/www/test --dry-run
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: JSON output
echo "Test 4: JSON output"
output=$($SCRIPT example.com /var/www/test --json --dry-run)
echo "$output" | jq . >/dev/null 2>&1
[ $? -eq 0 ] && echo "✅ PASS (valid JSON)" || echo "❌ FAIL (invalid JSON)"
```

---

## 🎓 Best Practices

### DO ✅
- Use `set -e` for error handling
- Validate all parameters
- Provide `--help` documentation
- Support multiple OS distributions
- Use standard exit codes
- Output JSON for automation
- Make scripts idempotent
- Use meaningful variable names
- Add verbose logging option
- Test with dry-run mode

### DON'T ❌
- Hardcode paths or values
- Depend on Python/GTK
- Mix stderr and stdout
- Ignore error conditions
- Use cryptic variable names
- Skip parameter validation
- Assume single OS/distro
- Print secrets to stdout
- Use `eval` or `exec` unsafely
- Forget to document usage

---

## 📚 Resources

**Similar Projects:**
- VestaCP: https://vestacp.com/docs/
- cPanel CLI: https://docs.cpanel.net/
- aaPanel: https://www.aapanel.com/
- ISPConfig: https://www.ispconfig.org/

**Shell Scripting:**
- Advanced Bash-Scripting Guide
- Google Shell Style Guide
- ShellCheck (linting tool)

---

**Version**: 1.0  
**Last Updated**: 9 Kasım 2025  
**Maintained by**: Orkesta Team
