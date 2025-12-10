#!/usr/bin/env bash
set -euo pipefail

# Ensure predictable permissions for created files/directories
umask 022

# Simple .deb builder for Orkesta
# Usage: ./packaging/build_deb.sh [version]

PKG_NAME="orkesta"
VERSION="${1:-0.1.0}"

# Use a temporary build dir on a filesystem that supports UNIX permissions
TMPROOT=$(mktemp -d)
BUILD_DIR="$TMPROOT/${PKG_NAME}_${VERSION}"
FINAL_OUTPUT_DIR="$(pwd)"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/$PKG_NAME"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# Control file
cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, python3-psutil, python3-yaml
Maintainer: Your Name <you@example.com>
Description: Orkesta - Web Development Environment Manager
 Orkesta is a GTK4/Libadwaita GUI application to help manage Apache, MySQL and PHP for developers.
EOF

# Optional: set maintainer scripts here (postinst/prerm) if needed

# Add maintainer scripts to install/remove sudoers entry allowing
# running Orkesta scripts without password for members of 'sudo' group.
# This is a pragmatic shortcut for desktop usage where GUI cannot prompt
# for a password. Consider replacing with a polkit/pkexec flow for
# better security in the long term.
cat > "$BUILD_DIR/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
# Create sudoers file to allow running orkesta scripts without password
SUDOERS_FILE=/etc/sudoers.d/orkesta
cat > "$SUDOERS_FILE" <<'EOL'
# Orkesta: allow members of 'sudo' group to run Orkesta scripts without password
%sudo ALL=(ALL) NOPASSWD: /opt/orkesta/scripts/*
EOL
chmod 0440 "$SUDOERS_FILE" || true
exit 0
POSTINST
chmod 0755 "$BUILD_DIR/DEBIAN/postinst"

cat > "$BUILD_DIR/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
case "$1" in
  remove|purge)
    rm -f /etc/sudoers.d/orkesta || true
    ;;
esac
exit 0
POSTRM
chmod 0755 "$BUILD_DIR/DEBIAN/postrm"

# Copy project to /opt/orkesta
rsync -a --exclude='.git' --exclude='build' --exclude='packaging' ./ "$BUILD_DIR/opt/$PKG_NAME/"

# Copy desktop entry and icon from packaging folder
if [ -f "packaging/usr/share/applications/orkesta.desktop" ]; then
  cp packaging/usr/share/applications/orkesta.desktop "$BUILD_DIR/usr/share/applications/"
fi

if [ -f "packaging/usr/share/icons/hicolor/scalable/apps/orkesta.svg" ]; then
  cp packaging/usr/share/icons/hicolor/scalable/apps/orkesta.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/orkesta.svg"
fi

# Wrapper executable
if [ -f "packaging/usr/bin/orkesta" ]; then
  cp packaging/usr/bin/orkesta "$BUILD_DIR/usr/bin/orkesta"
  chmod 755 "$BUILD_DIR/usr/bin/orkesta"
else
  cat > "$BUILD_DIR/usr/bin/orkesta" <<WRAP
#!/usr/bin/env bash
exec python3 /opt/${PKG_NAME}/main.py "$@"
WRAP
  chmod 755 "$BUILD_DIR/usr/bin/orkesta"
fi

# Ensure permissions
chmod -R 755 "$BUILD_DIR/opt/$PKG_NAME"

# Fix permissions to satisfy dpkg-deb checks (DEBIAN control dir must not be 0777)
# Directories should be at most 0775 and at least 0755; files default to 0644.
find "$BUILD_DIR" -type d -exec chmod 0755 {} +
find "$BUILD_DIR" -type f -exec chmod 0644 {} +

# DEBIAN maintainer scriptleri dpkg-deb tarafından yürütülebilir olmalıdır;
# yukarıdaki find komutu tüm dosyaları 0644 yaptıktan sonra burada tekrar
# postinst/postrm için exec biti yeniden veriyoruz.
if [ -f "$BUILD_DIR/DEBIAN/postinst" ]; then
  chmod 0755 "$BUILD_DIR/DEBIAN/postinst" || true
fi
if [ -f "$BUILD_DIR/DEBIAN/postrm" ]; then
  chmod 0755 "$BUILD_DIR/DEBIAN/postrm" || true
fi

# Ensure executables keep exec bit (wrapper and any scripts)
if [ -f "$BUILD_DIR/usr/bin/orkesta" ]; then
  chmod 0755 "$BUILD_DIR/usr/bin/orkesta"
fi
chmod -R 0755 "$BUILD_DIR/opt/$PKG_NAME"/scripts 2>/dev/null || true

# Build the package (requires dpkg-deb)
OUTPUT_DEB="${PKG_NAME}_${VERSION}.deb"
if command -v dpkg-deb >/dev/null 2>&1; then
  # Ensure critical permissions for dpkg-deb
  chmod 0755 "$BUILD_DIR" || true
  chmod 0755 "$(dirname "$BUILD_DIR")" || true
  chmod 0755 "$BUILD_DIR/DEBIAN" || true
  chmod 0644 "$BUILD_DIR/DEBIAN/control" || true

  dpkg-deb --build "$BUILD_DIR" "$OUTPUT_DEB"
  echo "Built $OUTPUT_DEB"
else
  echo "dpkg-deb not found. The package directory is at: $BUILD_DIR"
  echo "Install dpkg-deb (apt install dpkg-dev) and re-run to build the .deb." >&2
fi

# Move generated .deb back to project root if created in temp
if [ -f "$OUTPUT_DEB" ]; then
  # Avoid mv error when source and destination are the same path
  SRC_REAL=$(readlink -f "$OUTPUT_DEB") || SRC_REAL="$OUTPUT_DEB"
  DST_REAL=$(readlink -f "$FINAL_OUTPUT_DIR/$OUTPUT_DEB") || DST_REAL="$FINAL_OUTPUT_DIR/$OUTPUT_DEB"
  if [ "$SRC_REAL" != "$DST_REAL" ]; then
    mv -f "$OUTPUT_DEB" "$FINAL_OUTPUT_DIR/"
    echo "Moved $OUTPUT_DEB to $FINAL_OUTPUT_DIR/"
  else
    echo "$OUTPUT_DEB already in $FINAL_OUTPUT_DIR/"
  fi
fi

# Copy build folder back into repository for inspection (optional)
if [ -d "$BUILD_DIR" ]; then
  mkdir -p "$(pwd)/build"
  rm -rf "$(pwd)/build/${PKG_NAME}_${VERSION}"
  cp -a "$BUILD_DIR" "$(pwd)/build/"
fi

# Cleanup temp
rm -rf "$TMPROOT"
