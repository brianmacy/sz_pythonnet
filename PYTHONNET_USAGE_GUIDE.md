# Using Senzing C# SDK from Python via Python.NET

## Overview

This guide documents the actual implementation in this repository for using the Senzing C# SDK from Python on Windows using Python.NET (pythonnet).

**Why Python.NET for Windows:**
- Avoids Python version/distribution fragmentation
- Leverages officially supported C# SDK
- Single maintenance path for Windows platform
- Natural .NET integration for Windows environments

## Prerequisites

### Required Software

1. **Python 3.11, 3.12, or 3.13 (x64)**
   - Note: Python 3.14 not yet supported by pythonnet
2. **.NET Framework 4.x** (included with Windows)
3. **Python.NET (pythonnet)**: `pip install pythonnet`
4. **Senzing SDK 4.x** for Windows

### Installation

```bash
pip install pythonnet

# Verify installation
python -c "import clr; print('Python.NET installed successfully')"
```

## Project Structure

```
sz_pythonnet/
├── config.json.example          # Configuration template
├── config.json                  # Your configuration (not in git)
├── initialize_config.py         # Database initialization
├── add_data_sources.py          # Add CUSTOMERS/EMPLOYEES data sources
├── senzing_python_net_example.py # Working example with SenzingClient class
└── PYTHONNET_USAGE_GUIDE.md    # This file
```

## Configuration

### Step 1: Create config.json

Copy `config.json.example` to `config.json`:

```json
{
  "python": {
    "version": "3.12",
    "dll_path": "c:\\python312\\python312.dll"
  },
  "senzing": {
    "senzing_root": "C:\\path\\to\\senzing"
  }
}
```

**Important paths calculated from `senzing_root`:**
- SDK: `{senzing_root}/er/sdk/dotnet/extracted/lib/netstandard2.0`
- Database: `{senzing_root}/er/var/sqldb/G2C.db`
- Config: `{senzing_root}/er/etc`
- Resources: `{senzing_root}/er/resources`
- Support: `{senzing_root}/data`

### Step 2: Initialize Database

```bash
python initialize_config.py
```

This registers the default configuration in the Senzing database.

### Step 3: Add Data Sources

```bash
python add_data_sources.py
```

This adds CUSTOMERS and EMPLOYEES data sources to the configuration.

## Architecture

```
Python Application (senzing_python_net_example.py)
    ↓
Python.NET (clr module)
    ↓
C# SDK (Senzing.Sdk.dll)
    ↓
Native Core (libSz.dll, libSzConfig.dll)
    ↓
SQLite Database (G2C.db)
```

## Implementation Pattern

### Python.NET Runtime Configuration

**Critical: Configure runtime BEFORE importing clr:**

```python
import os
os.environ["PYTHONNET_PYDLL"] = "c:\\python312\\python312.dll"

try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx
    runtime = get_netfx()
    set_runtime(runtime)
except Exception:
    pass  # Default runtime will be used

import clr  # Must come AFTER runtime configuration
```

### Loading Senzing Assemblies

```python
import clr
import sys
from pathlib import Path

# Add SDK path
sdk_path = r"C:\senzing\er\sdk\dotnet\extracted\lib\netstandard2.0"
sys.path.append(sdk_path)

# Load assemblies
clr.AddReference("Senzing.Sdk")

# Import types
from Senzing.Sdk.Core import SzCoreEnvironment
from Senzing.Sdk import SzFlag
```

### SenzingClient Class

Our implementation provides a simplified `SenzingClient` class (see senzing_python_net_example.py:72):

```python
class SenzingClient:
    def __init__(self, sdk_path: str, settings: Dict[str, Any]):
        """Initialize Senzing client with configuration"""
        # Load assemblies, build environment, get services

    def add_record(self, data_source: str, record_id: str,
                   record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a record and return affected entities"""

    def delete_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """Delete a record and return affected entities"""

    def get_entity_by_record(self, data_source: str,
                             record_id: str) -> Dict[str, Any]:
        """Get entity by record key"""

    def get_entity_by_id(self, entity_id: int) -> Dict[str, Any]:
        """Get entity by entity ID"""

    def get_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """Get specific record"""

    def search_by_attributes(self, attributes: Dict[str, str]) -> Dict[str, Any]:
        """Search for entities by attributes"""

    def reevaluate_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """Reevaluate a record after configuration changes"""

    def why_entities(self, entity_id1: int, entity_id2: int) -> Dict[str, Any]:
        """Explain why two entities resolved or didn't"""

    def how_entity(self, entity_id: int) -> Dict[str, Any]:
        """Explain how an entity was constructed"""

    def export_json_entities(self, max_entities: int = None):
        """Export entities as JSON (iterator)"""

    def count_redo_records(self) -> int:
        """Get count of pending redo records"""

    def process_redo_records(self, max_records: int = 10):
        """Process pending redo records (iterator)"""
```

## Usage Example

```python
from pathlib import Path
import json

# Load configuration
CONFIG = load_config()
senzing_root = Path(CONFIG["senzing"]["senzing_root"])
dotnet_sdk_path = str(senzing_root / "er" / "sdk" / "dotnet" / "extracted" / "lib" / "netstandard2.0")

settings = {
    "PIPELINE": {
        "CONFIGPATH": str(senzing_root / "er" / "etc"),
        "RESOURCEPATH": str(senzing_root / "er" / "resources"),
        "SUPPORTPATH": str(senzing_root / "data")
    },
    "SQL": {
        "CONNECTION": f"sqlite3://na:na@{senzing_root}/er/var/sqldb/G2C.db"
    }
}

# Use context manager for automatic cleanup
with SenzingClient(dotnet_sdk_path, settings) as client:
    # Get version
    version = client.get_version()
    print(f"Senzing Version: {version['VERSION']}")

    # Add a record
    record = {
        "NAME_FIRST": "John",
        "NAME_LAST": "Doe",
        "PHONE_NUMBER": "702-555-1212",
        "EMAIL_ADDRESS": "johndoe@example.com"
    }
    result = client.add_record("CUSTOMERS", "CUST001", record)
    print(f"Affected entities: {result['AFFECTED_ENTITIES']}")

    # Retrieve entity
    entity = client.get_entity_by_record("CUSTOMERS", "CUST001")
    entity_id = entity["RESOLVED_ENTITY"]["ENTITY_ID"]

    # Search
    search_results = client.search_by_attributes({
        "NAME_FIRST": "John",
        "NAME_LAST": "Doe"
    })

    # Delete record
    delete_result = client.delete_record("CUSTOMERS", "CUST001")
```

## Common Flags

The SenzingClient class uses these flag combinations:

### Entity Retrieval
```python
flags = (SzFlag.SzEntityIncludeEntityName
         | SzFlag.SzEntityIncludeRecordSummary
         | SzFlag.SzEntityIncludeRecordData)
```

### Search
```python
flags = (SzFlag.SzSearchIncludeResolved
         | SzFlag.SzIncludeFeatureScores)
```

### Export
```python
flags = (SzFlag.SzExportIncludeMultiRecordEntities
         | SzFlag.SzExportIncludeSingleRecordEntities)
```

### Write Operations (Add/Delete)
```python
flags = SzFlag.SzWithInfo  # Return affected entities
```

## Type Conversions

### Python to .NET

```python
# Strings and integers - direct usage
client.add_record("CUSTOMERS", "REC123", record_dict)
entity = client.get_entity_by_id(123)

# JSON - use json.dumps/loads
record_json = json.dumps({"NAME_FIRST": "John"})
entity = json.loads(entity_json)
```

### .NET Collections (for advanced usage)

```python
from System.Collections.Generic import HashSet, List
from System import Tuple

# HashSet[int]
entity_ids = HashSet[int]()
entity_ids.Add(100)

# HashSet[Tuple[str, str]]
record_keys = HashSet[Tuple[str, str]]()
record_keys.Add(Tuple.Create("CUSTOMERS", "REC123"))

# List[str]
sources = List[str]()
sources.Add("CUSTOMERS")
```

## Error Handling

```python
from Senzing.Sdk import (
    SzException,
    SzNotFoundException,
    SzUnknownDataSourceException,
    SzBadInputException
)

try:
    entity = client.get_entity_by_record("CUSTOMERS", "REC123")
except SzNotFoundException as e:
    print(f"Record not found: {e}")
except SzUnknownDataSourceException as e:
    print(f"Unknown data source: {e}")
except SzBadInputException as e:
    print(f"Bad input: {e}")
except SzException as e:
    print(f"General Senzing error: {e}")
```

## Running the Examples

### Complete Working Example

```bash
# Run the complete example
python senzing_python_net_example.py
```

This demonstrates:
- Loading configuration from config.json
- Adding records to CUSTOMERS and EMPLOYEES
- Retrieving entities
- Searching by attributes
- Why/How explainability
- Deleting records

## Troubleshooting

### Assembly Not Found

**Error**: `Could not load file or assembly 'Senzing.Sdk'`

**Solution**:
1. Verify SDK path in config.json
2. Check `Senzing.Sdk.dll` exists in the SDK path
3. Ensure `sys.path.append()` is called before `clr.AddReference()`

### Python DLL Error

**Error**: `Failed to initialize Python.Runtime.dll`

**Solution**:
1. Verify Python version is 3.11, 3.12, or 3.13 (x64)
2. Update `PYTHONNET_PYDLL` path in config.json
3. Ensure path points to correct pythonXXX.dll file

### Database Connection Error

**Error**: `No engine configuration registered in datastore`

**Solution**: Run `initialize_config.py` to initialize the database

**Error**: `Data source code [CUSTOMERS] does not exist`

**Solution**: Run `add_data_sources.py` to add data sources

### PATH Environment Variable

Ensure Senzing native libraries are in PATH:

```powershell
# PowerShell
$env:PATH = "C:\senzing\er\lib;$env:PATH"
python senzing_python_net_example.py
```

```cmd
:: Command Prompt
set PATH=C:\senzing\er\lib;%PATH%
python senzing_python_net_example.py
```

## Performance Considerations

- **Connection Pooling**: Managed automatically by C# SDK
- **Memory Management**: Python.NET handles garbage collection
- **Resource Cleanup**: Always use context managers (`with` statement)
- **Database Choice**: SQLite for development, PostgreSQL/SQL Server for production

## Additional Resources

- **C# SDK Documentation**: Senzing SDK documentation
- **Python.NET Documentation**: https://pythonnet.github.io/
- **Senzing Documentation**: https://docs.senzing.com/

## License

Senzing C# SDK is proprietary software. Python.NET is licensed under MIT.
