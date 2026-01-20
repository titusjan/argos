# CLAUDE.md - Argos Project Guide

## Project Overview

Argos is a GUI application for viewing and exploring multi-dimensional scientific data, written in Python and Qt (PyQt5). It provides interactive visualization through multiple inspector types (Line Plot, Image Plot, Table, Text) with real-time configuration updates.

**Version**: 0.4.4
**License**: GPLv3
**Repository**: https://github.com/titusjan/argos

## Quick Commands

```bash
# Run the application
python -m argos
# or
argos [FILE ...]

# Run tests
python setup.py test

# Run with coverage
coverage run --source argos setup.py test
coverage report -m

# Lint code
flake8 argos tests
pylint argos

# Build documentation
make docs

# Create distribution
make dist
```

## Project Structure

```
argos/
├── argos/                    # Main package
│   ├── __main__.py          # CLI entry point (python -m argos)
│   ├── main.py              # Main application entry
│   ├── application.py       # ArgosApplication class
│   ├── info.py              # Version and metadata
│   │
│   ├── collect/             # Data collection and slicing system
│   ├── config/              # Configuration tree items (CTI system)
│   ├── inspector/           # Data visualization inspectors
│   │   ├── pgplugins/       # PyQtGraph-based inspectors
│   │   └── qtplugins/       # Qt-based inspectors
│   ├── repo/                # Repository/data management
│   │   ├── rtiplugins/      # File format plugins (HDF5, NetCDF, etc.)
│   │   └── detailplugins/   # Detail view plugins
│   ├── widgets/             # UI components (MainWindow, dialogs)
│   ├── qt/                  # Qt abstraction layer
│   ├── reg/                 # Plugin registry system
│   ├── utils/               # Utility modules
│   ├── external/            # Bundled external libraries
│   └── img/                 # UI assets (icons, logos)
│
├── tests/                   # Test suite
├── docs/                    # Sphinx documentation
├── development/             # Development notes and guidelines
├── pyproject.toml           # Project configuration
├── setup.py                 # Setup script
└── Makefile                 # Development targets
```

## Key Technologies

- **Python 3.7+** (tested on 3.7-3.10)
- **PyQt5** - GUI framework
- **NumPy** - Array operations (required)
- **PyQtGraph** - Scientific plotting
- **CmLib** - Color map library

Optional dependencies for file formats:
- h5py (HDF5), netCDF4 (NetCDF), pillow (images), scipy (MATLAB/WAV), pandas (CSV)

## Architecture

### Plugin System

Argos uses a plugin architecture with three main plugin types:

1. **RTI Plugins** (`repo/rtiplugins/`): File format handlers (Repository Type Items)
2. **Inspector Plugins** (`inspector/`): Visualization types (line plots, images, tables)
3. **Detail Plugins** (`repo/detailplugins/`): Metadata views (attributes, properties)

All plugins use a registry pattern defined in `reg/basereg.py`.

### Configuration System (CTI)

The Config Tree Item (CTI) system in `config/` provides hierarchical, type-safe configuration:

- `AbstractCti` - Base class for all config items
- Type-specific: `BoolCti`, `IntCti`, `FloatCti`, `StringCti`, `ChoiceCti`
- `GroupCti` - Container for nested config items
- Qt integration via `ConfigTreeModel` and `ConfigTreeView`

### Data Model

- **RTI (Repository Type Item)**: Base class for all data items in `repo/baserti.py`
- **Collector**: Manages array slicing and dimension selection in `collect/`
- **RepoTreeModel**: Qt model for the data repository tree

## Code Conventions

- Follow PEP 8 style guidelines
- Use docstrings for public classes and methods
- Configuration items (CTI) should inherit from appropriate base class
- Plugins register themselves via the registry system
- UI widgets go in `widgets/`, Qt abstractions in `qt/`

## Settings Location

- **macOS**: `~/Library/Preferences/titusjan/argos/settings.json`
- **Linux**: `~/.config/titusjan/argos/settings.json`
- **Windows**: `C:\Users\<user>\AppData\Local\titusjan\argos\settings.json`

## Development Notes

- The main window is in `widgets/mainwindow.py`
- Application startup logic is in `main.py` and `application.py`
- To add a new file format, create a plugin in `repo/rtiplugins/`
- To add a new visualization, create an inspector in `inspector/`
- Use `make clean` to remove build artifacts before fresh builds
