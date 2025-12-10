Orkesta packaging helper

This folder contains a simple helper to build a .deb package for the project.

Usage:
  chmod +x packaging/build_deb.sh
  ./packaging/build_deb.sh 0.1.0

What the script does:
- Creates a directory layout for a Debian package
- Copies the project into `/opt/orkesta`
- Installs a wrapper into `/usr/bin/orkesta`
- Installs a .desktop file and a scalable SVG icon into the hicolor icon theme
- Generates a .deb using `dpkg-deb --build`

Notes:
- The package `Depends` in the control file lists runtime system packages that must be installed (GTK, gir bindings, python3 libs). Adjust as needed.
- Packaging does NOT install Python pip dependencies. Prefer to depend on distribution packages where possible or bundle a virtualenv into the package.
- For production-quality packaging consider using `debhelper`/`dpkg-buildpackage` and proper `debian/` layout.
