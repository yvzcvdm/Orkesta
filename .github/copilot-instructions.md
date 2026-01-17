# Orkesta - AI Coding Assistant Instructions

## Project Overview

Orkesta is a **modular GTK4/Libadwaita desktop application** for managing local web development environments (Apache, MySQL, PHP, etc.) on Linux. Written in Python, it follows a **script-first architecture** where bash scripts handle all system operations and Python provides the UI layer.

## Core Architecture Principles

### 1. Script-First Approach (Critical)
**The defining principle of this codebase**: All system operations are performed by standalone bash scripts, NOT Python code.

- **Python services** (`services/*.py`) are thin wrappers that call bash scripts
- **Bash scripts** (`scripts/*.sh`) contain all business logic, OS detection, and system operations
- One sudo password prompts once at script execution, not per-operation
- Scripts are CLI-first and can be used independently of the GUI

```python
# ✅ CORRECT: Service calls script
def install(self):
    return self._execute_script('apache.sh', 'install', timeout=600)

# ❌ WRONG: Service contains system logic
def install(self):
    subprocess.run(['dnf', 'install', 'httpd'])  # Never do this!
```

### 2. Minimal Main, Maximum Modularity
- `main.py` ONLY launches GTK - contains zero business logic
- `src/app.py` initializes GTK application and window
- All service logic lives in `services/` modules
- Never put service operations in main entry points

### 3. Service = Module + Scripts Pattern
Each service follows this exact structure:
```
services/apache.py          # Python class inheriting BaseService
scripts/apache.sh           # Bash script with OS detection + operations
```

### 4. Dynamic Service Loading
- `ServiceLoader` auto-discovers modules in `services/` directory
- Any `.py` file (except `_*` and `base_service.py`) with BaseService subclass is loaded
- Add new service = drop Python file in `services/`, ensure it inherits `BaseService`

## Key Components

### Platform Detection (`src/platform_manager.py`)
- **Read-only**: Detects OS type (Fedora/Debian/Ubuntu/Arch) and package manager
- Never performs operations, only provides system information
- Scripts perform their own OS detection for independence

### Service Base Class (`services/base_service.py`)
All services must inherit from `BaseService` and implement:
- `name` property (required)
- `is_installed()`, `install()`, `uninstall()` methods
- Script execution via `_execute_script()` helper

### Bash Scripts (`scripts/*.sh`)
- First 20 lines: OS detection logic setting `OS_TYPE` variable
- Support Fedora (dnf), Debian/Ubuntu (apt), Arch (pacman)
- Action-based CLI: `script.sh <action> [args]`
- Return codes: 0 = success, non-zero = failure
- For data queries, print structured output (JSON preferred)

### UI Layer (`src/ui/main_window.py`)
- GTK4 + Libadwaita components
- Two-page navigation: service list ↔ service detail
- Detail pages customized per-service (VHost list for Apache, DB list for MySQL)
- Async operations with progress dialogs prevent UI freezing

## Development Workflows

### Adding a New Service

1. Create `services/newservice.py`:
```python
from services.base_service import BaseService, ServiceType

class NewService(BaseService):
    SCRIPT_NAME = 'newservice.sh'
    
    @property
    def name(self) -> str:
        return "newservice"
    
    def is_installed(self) -> bool:
        success, output = self._execute_script(self.SCRIPT_NAME, 'is-installed')
        return success and output.strip().lower() == 'true'
    
    def install(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'install', timeout=600)
```

2. Create `scripts/newservice.sh` with OS detection + actions
3. Service auto-loads on next app launch (no registration needed)

### Running the Application

```bash
# Development mode (from project root)
python3 main.py

# With specific language
LANGUAGE=en python3 main.py  # English
LANGUAGE=tr python3 main.py  # Turkish
```

### Translation Workflow

Using GNU gettext system:
```bash
# Extract, update, compile all translations
python3 translations.py

# Translations stored in locale/{lang}/LC_MESSAGES/orkesta.po
```

In code, wrap user-visible strings:
```python
from src.utils.i18n import get_i18n
_ = get_i18n().get_translator()

label = Gtk.Label(label=_("Install"))  # ✅ Translatable
```

### Testing Services

Scripts can be tested independently:
```bash
# Test Apache script directly
sudo scripts/apache.sh is-installed
sudo scripts/apache.sh install
sudo scripts/apache.sh vhost-create example.com /var/www/example
```

## Project Conventions

### File Organization
- `src/` - Core application (app, platform detection, service loader)
- `src/ui/` - GTK UI components
- `src/utils/` - Utilities (i18n, logging, validators, system helpers)
- `services/` - Service Python modules (UI interface layer)
- `scripts/` - Bash scripts (system operation layer)
- `references/` - Architecture documentation (read these!)
- `locale/` - Translations (gettext .po/.mo files)

### Naming Conventions
- Services: lowercase property names (`apache`, `mysql`, not `Apache`)
- Script actions: kebab-case (`vhost-create`, `is-installed`)
- Python: snake_case for methods, PascalCase for classes
- Bash: snake_case for functions

### Error Handling
- Scripts: Exit with non-zero code on error
- Python services: Return `Tuple[bool, str]` (success, message)
- UI: Show errors in dialogs with user-friendly messages

### Dependencies
- **Required**: Python 3.10+, GTK4, Libadwaita, systemd
- **Per-distro package manager**: dnf, apt, or pacman
- No pip dependencies beyond standard library (system packages only)

## Common Pitfalls

1. **Don't put bash commands in Python** - Create/modify scripts instead
2. **Don't create services in main.py** - Use ServiceLoader auto-discovery
3. **Don't hardcode OS-specific logic in Python** - Scripts handle OS differences
4. **Don't forget translations** - Wrap all UI strings in `_()`
5. **Don't block UI thread** - Use `GLib.idle_add()` for long operations

## Integration Points

### Service → Script Communication
Services call scripts via `_execute_script()` inherited from BaseService:
- Constructs full script path from `SCRIPTS_DIR + service.SCRIPT_NAME`
- Executes with `pkexec` for privilege escalation
- Parses stdout/stderr and return codes

### UI → Service Communication
`MainWindow` accesses services through `ServiceLoader`:
```python
service = self.service_loader.get_service('apache')
success, msg = service.install()
```

### Cross-Service Dependencies
Apache ↔ PHP integration example:
- Apache service detects available PHP versions via script
- PHP service manages versions independently
- Apache switches PHP via `a2enmod`/`a2dismod` script actions

## References

For deeper architectural understanding, read in order:
1. [references/ARCHITECTURE_SUMMARY.md](references/ARCHITECTURE_SUMMARY.md) - Core principles
2. [references/PROJECT_REFERENCE.md](references/PROJECT_REFERENCE.md) - Complete reference
3. [references/CURRENT_STATUS.md](references/CURRENT_STATUS.md) - What's implemented

These documents are the source of truth for design decisions.
