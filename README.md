# Senzing C# SDK via Python.NET

Python.NET integration for using the Senzing C# SDK on Windows.

## Overview

This repository demonstrates using the Senzing C# SDK from Python on Windows using Python.NET (pythonnet). This approach leverages the officially supported C# SDK while maintaining Python's ease of use.

**Why Python.NET?**
- Single maintenance path for Windows
- Leverages well-tested C# SDK
- Avoids Python distribution fragmentation
- Natural .NET integration on Windows

## Requirements

- **Python**: 3.11, 3.12, or 3.13 (x64 only)
  - *Note: Python 3.14 not yet supported by pythonnet*
- **pythonnet**: `pip install pythonnet`
- **.NET Framework**: 4.x (included with Windows)
- **Senzing SDK**: Version 4.x for Windows

## Quick Start

### 1. Install Python.NET

```bash
pip install pythonnet
```

### 2. Configure

Copy `config.json.example` to `config.json` and update paths:

```json
{
  "python": {
    "version": "3.12",
    "dll_path": "c:\\python312\\python312.dll"
  },
  "senzing": {
    "senzing_root": "C:\\your\\senzing\\installation"
  }
}
```

### 3. Initialize Database

```bash
python initialize_config.py
```

### 4. Add Data Sources

```bash
python add_data_sources.py
```

### 5. Run Example

```bash
python senzing_python_net_example.py
```

## Project Files

| File | Purpose |
|------|---------|
| `config.json.example` | Configuration template |
| `initialize_config.py` | Initialize Senzing database |
| `add_data_sources.py` | Add CUSTOMERS and EMPLOYEES data sources |
| `senzing_python_net_example.py` | **Complete working example** |
| `PYTHONNET_USAGE_GUIDE.md` | **Comprehensive usage documentation** |
| `.github/workflows/lint.yml` | CI linting workflow |

## Example Usage

```python
from senzing_python_net_example import SenzingClient

# Define SDK path
sdk_path = r"C:\senzing\er\sdk\dotnet\extracted\lib\netstandard2.0"

# Configuration
settings = {
    "PIPELINE": {
        "CONFIGPATH": r"C:\senzing\er\etc",
        "RESOURCEPATH": r"C:\senzing\er\resources",
        "SUPPORTPATH": r"C:\senzing\data"
    },
    "SQL": {
        "CONNECTION": "sqlite3://na:na@C:\\senzing\\er\\var\\sqldb\\G2C.db"
    }
}

# Use client
with SenzingClient(sdk_path, settings) as client:
    # Add record
    result = client.add_record("CUSTOMERS", "CUST001", {
        "NAME_FIRST": "John",
        "NAME_LAST": "Doe",
        "PHONE_NUMBER": "702-555-1212"
    })

    # Get entity
    entity = client.get_entity_by_record("CUSTOMERS", "CUST001")

    # Search
    results = client.search_by_attributes({
        "NAME_FIRST": "John",
        "NAME_LAST": "Doe"
    })
```

## SenzingClient API

The `SenzingClient` class provides a simplified interface:

- `add_record()` - Add a record
- `delete_record()` - Delete a record
- `get_entity_by_record()` - Get entity by record key
- `get_entity_by_id()` - Get entity by ID
- `get_record()` - Get specific record
- `search_by_attributes()` - Search for entities
- `reevaluate_record()` - Reevaluate after config changes
- `why_entities()` - Explain entity relationships
- `how_entity()` - Explain entity construction
- `export_json_entities()` - Export entities (iterator)
- `count_redo_records()` - Count pending redos
- `process_redo_records()` - Process redos (iterator)

See [`PYTHONNET_USAGE_GUIDE.md`](PYTHONNET_USAGE_GUIDE.md) for complete documentation.

## Architecture

```
Python Application
    ↓
Python.NET (pythonnet)
    ↓
C# SDK (Senzing.Sdk.dll)
    ↓
Native Core (libSz.dll)
    ↓
SQLite/PostgreSQL Database
```

## Troubleshooting

### Assembly Not Found

Verify SDK path in `config.json` points to:
```
C:\senzing\er\sdk\dotnet\extracted\lib\netstandard2.0
```

### Python DLL Error

Ensure `PYTHONNET_PYDLL` in `config.json` matches your Python installation:
- Python 3.11: `c:\python311\python311.dll`
- Python 3.12: `c:\python312\python312.dll`
- Python 3.13: `c:\python313\python313.dll`

### No Configuration Registered

Run `python initialize_config.py` to initialize the database.

### Data Source Not Found

Run `python add_data_sources.py` to add CUSTOMERS and EMPLOYEES data sources.

### PATH Issues

Ensure Senzing native libraries are in PATH:

```powershell
$env:PATH = "C:\senzing\er\lib;$env:PATH"
```

## Development

### Linting

```bash
# Install linting tools
pip install flake8 pylint

# Run linters
python -m flake8 --max-line-length=120 --ignore=E402,E501,W503,F541 *.py
python -m pylint --max-line-length=120 *.py
```

### CI/CD

GitHub Actions automatically runs linting on push and pull requests. See `.github/workflows/lint.yml`.

## Documentation

- [`PYTHONNET_USAGE_GUIDE.md`](PYTHONNET_USAGE_GUIDE.md) - Complete implementation guide
- [Python.NET Documentation](https://pythonnet.github.io/)
- [Senzing Documentation](https://docs.senzing.com/)

## License

Senzing C# SDK is proprietary software. Python.NET is licensed under MIT.

## Support

For questions or issues:
- Check the [PYTHONNET_USAGE_GUIDE.md](PYTHONNET_USAGE_GUIDE.md)
- Review the working example: `senzing_python_net_example.py`
- Contact Senzing support

## Notes

- **Windows Only**: This implementation is specific to Windows x64
- **Python Versions**: Only 3.11, 3.12, and 3.13 are supported
- **Database**: SQLite for development, PostgreSQL/SQL Server for production
- **Testing**: Test thoroughly in your specific environment
