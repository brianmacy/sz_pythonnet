# Using Senzing C# SDK with Python.NET

## Overview

This guide explains how to use the Senzing C# SDK from Python using Python.NET (pythonnet). This approach is particularly useful for Python developers on **Windows and macOS** where native Python support may be limited.

**Note:** Senzing provides native Python support on Linux. The Senzing SDK also supports Java on all platforms. This guide focuses on the Python.NET path for Windows and macOS development.

**Why Python.NET:**
- Access Senzing from Python on Windows and macOS, directly without a client/server setup
- Direct access to officially supported C# SDK
- No wrapper maintenance overhead
- Full access to all SDK methods and features
- Cross-platform .NET support (Framework/Core)

## Prerequisites

### Required Software

1. **Python 3.11, 3.12, or 3.13 (x64)**
   - Python 3.14 not yet supported by pythonnet
2. **.NET Runtime** (Framework 4.x or Core 2.0+)
3. **pythonnet**: `pip install pythonnet`
4. **Senzing C# SDK**

### Installation

```bash
pip install pythonnet

# Verify
python -c "import clr; print('Python.NET ready')"
```

## Python.NET Fundamentals

### Loading .NET Assemblies

```python
import clr
import sys

# Add assembly location to path
sys.path.append(r"C:\path\to\assemblies")

# Load the assembly
clr.AddReference("Senzing.Sdk")

# Import .NET types
from Senzing.Sdk import SzEngine, SzFlag
from Senzing.Sdk.Core import SzCoreEnvironment
```

### Runtime Configuration

**Important:** Configure runtime BEFORE importing `clr`:

```python
import os

# Set Python DLL for pythonnet
os.environ["PYTHONNET_PYDLL"] = r"c:\python312\python312.dll"

# Choose runtime (.NET Framework or .NET Core)
try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx  # or get_coreclr for cross-platform
    runtime = get_netfx()
    set_runtime(runtime)
except Exception:
    pass  # Default runtime will be used

import clr  # MUST come after runtime config
```

## Initializing Senzing

### Building the Environment

```python
import json
from Senzing.Sdk.Core import SzCoreEnvironment

settings = {
    "PIPELINE": {
        "CONFIGPATH": r"C:\senzing\etc",
        "RESOURCEPATH": r"C:\senzing\resources",
        "SUPPORTPATH": r"C:\senzing\data"
    },
    "SQL": {
        "CONNECTION": "sqlite3://na:na@C:\\senzing\\database.db"
    }
}

settings_json = json.dumps(settings)

# Build environment using builder pattern
env = (SzCoreEnvironment.NewBuilder()
       .InstanceName("MyApp")
       .Settings(settings_json)
       .VerboseLogging(False)
       .Build())
```

### Getting Services

```python
# Get service instances
engine = env.GetEngine()
config_mgr = env.GetConfigManager()
product = env.GetProduct()
diagnostic = env.GetDiagnostic()

# Always destroy when done
env.Destroy()
```

## Core Operations

### Adding Records

```python
import json
from Senzing.Sdk import SzFlag

# Prepare record data
record_data = {
    "NAME_FIRST": "John",
    "NAME_LAST": "Doe",
    "PHONE_NUMBER": "702-555-1212",
    "EMAIL_ADDRESS": "john@example.com"
}

record_json = json.dumps(record_data)

# Add without info
engine.AddRecord("CUSTOMERS", "REC001", record_json)

# Add with resolution info
info_json = engine.AddRecord(
    "CUSTOMERS",          # data source code
    "REC001",             # record ID
    record_json,          # record JSON
    SzFlag.SzWithInfo     # flags
)

# Parse returned info
info = json.loads(info_json)
affected = info.get("AFFECTED_ENTITIES", [])
```

### Deleting Records

```python
# Delete and get affected entities
info_json = engine.DeleteRecord(
    "CUSTOMERS",
    "REC001",
    SzFlag.SzWithInfo
)

info = json.loads(info_json)
```

### Reevaluating Records

```python
# After configuration changes, reevaluate records
info_json = engine.ReevaluateRecord(
    "CUSTOMERS",
    "REC001",
    SzFlag.SzWithInfo
)
```

### Reevaluating Entities

```python
# Reevaluate entire entity by ID
info_json = engine.ReevaluateEntity(
    entity_id=12345,
    flags=SzFlag.SzWithInfo
)
```

## Redo Processing

```python
# Count pending redo records
count = engine.CountRedoRecords()
print(f"Pending redos: {count}")

# Process redo records
redo_record = engine.GetRedoRecord()
while redo_record is not None:
    info_json = engine.ProcessRedoRecord(redo_record, SzFlag.SzWithInfo)
    # Process info...
    redo_record = engine.GetRedoRecord()
```

## Retrieval Operations

### Get Entity by Record Key

```python
from Senzing.Sdk import SzFlag

# Combine flags with bitwise OR
flags = (SzFlag.SzEntityIncludeEntityName |
         SzFlag.SzEntityIncludeRecordData |
         SzFlag.SzEntityIncludeRelatedEntities)

entity_json = engine.GetEntity("CUSTOMERS", "REC001", flags)
entity = json.loads(entity_json)

entity_id = entity["RESOLVED_ENTITY"]["ENTITY_ID"]
entity_name = entity["RESOLVED_ENTITY"]["ENTITY_NAME"]
```

### Get Entity by Entity ID

```python
entity_json = engine.GetEntity(12345, SzFlag.SzEntityDefaultFlags)
entity = json.loads(entity_json)
```

### Get Record

```python
record_json = engine.GetRecord(
    "CUSTOMERS",
    "REC001",
    SzFlag.SzRecordDefaultFlags
)
record = json.loads(record_json)
```

### Get Virtual Entity

Combine multiple records into a hypothetical entity:

```python
from System.Collections.Generic import HashSet
from System import Tuple

# Create set of record keys
record_keys = HashSet[Tuple[str, str]]()
record_keys.Add(Tuple.Create("CUSTOMERS", "REC001"))
record_keys.Add(Tuple.Create("CUSTOMERS", "REC002"))
record_keys.Add(Tuple.Create("EMPLOYEES", "EMP001"))

virtual_json = engine.GetVirtualEntity(
    record_keys,
    SzFlag.SzVirtualEntityDefaultFlags
)
```

## Search Operations

### Search by Attributes

```python
search_attrs = {
    "NAME_FIRST": "John",
    "NAME_LAST": "Doe",
    "PHONE_NUMBER": "702-555-1212"
}

search_json = json.dumps(search_attrs)

# Default search
results_json = engine.SearchByAttributes(
    search_json,
    SzFlag.SzSearchByAttributesDefaultFlags
)

# With custom profile
results_json = engine.SearchByAttributes(
    search_json,
    "SEARCH",  # search profile name
    SzFlag.SzSearchIncludeResolved | SzFlag.SzIncludeFeatureScores
)

results = json.loads(results_json)
for entity_result in results.get("RESOLVED_ENTITIES", []):
    entity = entity_result["ENTITY"]["RESOLVED_ENTITY"]
    match_info = entity_result.get("MATCH_INFO", {})
    print(f"Entity {entity['ENTITY_ID']}: Score {match_info.get('MATCH_SCORE')}")
```

## Explainability Operations

### Why Entities

Explain relationship between two entities:

```python
why_json = engine.WhyEntities(
    entity_id1=100,
    entity_id2=200,
    flags=SzFlag.SzWhyEntitiesDefaultFlags | SzFlag.SzIncludeFeatureScores
)

why_results = json.loads(why_json)
```

### Why Records

```python
why_json = engine.WhyRecords(
    "CUSTOMERS", "REC001",  # data source 1, record ID 1
    "EMPLOYEES", "EMP001",  # data source 2, record ID 2
    SzFlag.SzWhyRecordsDefaultFlags
)
```

### Why Record in Entity

```python
why_json = engine.WhyRecordInEntity(
    "CUSTOMERS",
    "REC001",
    SzFlag.SzWhyRecordInEntityDefaultFlags
)
```

### How Entity

Show how entity was constructed:

```python
how_json = engine.HowEntity(
    entity_id=12345,
    flags=SzFlag.SzHowEntityDefaultFlags
)

how_results = json.loads(how_json)
steps = how_results["HOW_RESULTS"]["RESOLUTION_STEPS"]
for step in steps:
    print(f"Step {step['STEP']}: {step.get('MATCH_INFO', {})}")
```

### Why Search

Explain why entity matched or didn't match search:

```python
search_attrs = json.dumps({"NAME_FIRST": "John", "NAME_LAST": "Doe"})

why_json = engine.WhySearch(
    search_attrs,
    entity_id=12345,
    None,  # optional search profile
    SzFlag.SzWhySearchDefaultFlags
)
```

## Network Analysis

### Find Path Between Entities

```python
from System.Collections.Generic import HashSet

# By entity IDs
avoid_entities = HashSet[int]()
avoid_entities.Add(999)  # Entities to avoid

path_json = engine.FindPath(
    start_entity_id=100,
    end_entity_id=200,
    max_degrees=4,
    avoided_entities=avoid_entities,
    required_data_sources=None,
    flags=SzFlag.SzFindPathDefaultFlags
)

# By record keys
from System import Tuple

avoid_records = HashSet[Tuple[str, str]]()
avoid_records.Add(Tuple.Create("CUSTOMERS", "REC999"))

path_json = engine.FindPath(
    "CUSTOMERS", "REC001",  # start
    "EMPLOYEES", "EMP001",  # end
    4,  # max degrees
    avoid_records,
    None,  # required sources
    SzFlag.SzFindPathDefaultFlags
)
```

### Find Network

```python
# By entity IDs
entity_ids = HashSet[int]()
entity_ids.Add(100)
entity_ids.Add(200)
entity_ids.Add(300)

network_json = engine.FindNetwork(
    entity_ids,
    max_degrees=3,
    build_out_degrees=1,
    build_out_max_entities=10,
    flags=SzFlag.SzFindNetworkDefaultFlags
)

# By record keys
record_keys = HashSet[Tuple[str, str]]()
record_keys.Add(Tuple.Create("CUSTOMERS", "REC001"))
record_keys.Add(Tuple.Create("EMPLOYEES", "EMP123"))

network_json = engine.FindNetwork(
    record_keys,
    3, 1, 10,
    SzFlag.SzFindNetworkDefaultFlags
)
```

### Find Interesting Entities

```python
# By entity ID
interesting_json = engine.FindInterestingEntities(
    entity_id=12345,
    flags=SzFlag.SzFindInterestingEntitiesDefaultFlags
)

# By record key
interesting_json = engine.FindInterestingEntities(
    "CUSTOMERS", "REC001",
    SzFlag.SzFindInterestingEntitiesDefaultFlags
)
```

## Export Operations

### Export JSON Entities

```python
# Start export
export_handle = engine.ExportJsonEntityReport(SzFlag.SzExportDefaultFlags)

try:
    json_data = engine.FetchNext(export_handle)
    while json_data is not None:
        entity = json.loads(json_data)
        # Process entity...
        print(f"Entity: {entity['RESOLVED_ENTITY']['ENTITY_ID']}")
        json_data = engine.FetchNext(export_handle)
finally:
    engine.CloseExport(export_handle)
```

### Export CSV Entities

```python
export_handle = engine.ExportCsvEntityReport(
    "*",  # column list (* = all columns)
    SzFlag.SzExportDefaultFlags
)

try:
    # First line is headers
    csv_headers = engine.FetchNext(export_handle)
    print(csv_headers)

    # Data rows
    csv_row = engine.FetchNext(export_handle)
    while csv_row is not None:
        print(csv_row)
        csv_row = engine.FetchNext(export_handle)
finally:
    engine.CloseExport(export_handle)
```

## Configuration Management

### Get Configuration Info

```python
config_mgr = env.GetConfigManager()

# Get default config ID
config_id = config_mgr.GetDefaultConfigID()

# Get config registry
registry_json = config_mgr.GetConfigRegistry()
registry = json.loads(registry_json)

for cfg in registry["CONFIGS"]:
    print(f"Config {cfg['CONFIG_ID']}: {cfg.get('CONFIG_COMMENTS')}")
```

### Create and Modify Configuration

```python
# Get current config
current_id = config_mgr.GetDefaultConfigID()
config = config_mgr.CreateConfig(current_id)

# Register new data source
config.RegisterDataSource("NEW_SOURCE")

# Export modified config
config_json = config.Export()

# Register new config
new_id = config_mgr.RegisterConfig(
    config_json,
    "Added NEW_SOURCE data source"
)

# Replace default (handles race conditions)
config_mgr.ReplaceDefaultConfigID(current_id, new_id)

# Hot-swap configuration
env.Reinitialize(new_id)
```

### Data Source Registry

```python
config = config_mgr.CreateConfig()

# Get data sources
ds_registry_json = config.GetDataSourceRegistry()
ds_registry = json.loads(ds_registry_json)

for ds in ds_registry["DATA_SOURCES"]:
    print(f"{ds['DSRC_CODE']}: ID {ds['DSRC_ID']}")
```

## Product and Diagnostic Info

### Product Version

```python
product = env.GetProduct()

version_json = product.GetVersion()
version = json.loads(version_json)
print(f"Version: {version['VERSION']}")

license_json = product.GetLicense()
license_info = json.loads(license_json)
print(f"Customer: {license_info.get('customer')}")
```

### Repository Diagnostics

```python
diagnostic = env.GetDiagnostic()

# Repository info
repo_json = diagnostic.GetRepositoryInfo()
repo = json.loads(repo_json)

entity_summary = repo["ENTITY_SUMMARY"]
print(f"Total entities: {entity_summary.get('TOTAL_ENTITIES')}")

# Data sources
for ds_code, ds_info in repo["DATA_SOURCES"].items():
    print(f"{ds_code}: {ds_info.get('RECORDS')} records")

# Performance check
perf_json = diagnostic.CheckRepositoryPerformance(seconds_to_run=10)
perf = json.loads(perf_json)
```

## Flags Reference

### Entity Retrieval

```python
from Senzing.Sdk import SzFlag

# Default entity detail
SzFlag.SzEntityDefaultFlags

# Minimal info
SzFlag.SzEntityBriefDefaultFlags

# Include options (combine with |)
SzFlag.SzEntityIncludeEntityName
SzFlag.SzEntityIncludeRecordSummary
SzFlag.SzEntityIncludeRecordData
SzFlag.SzEntityIncludeRecordMatchingInfo
SzFlag.SzEntityIncludeRecordJsonData
SzFlag.SzEntityIncludeRecordUnmappedData
SzFlag.SzEntityIncludeRecordFeatures
SzFlag.SzEntityIncludeRelatedEntities
SzFlag.SzEntityIncludeRelatedMatchingInfo
SzFlag.SzEntityIncludeRelatedRecordSummary

# Example: Full entity details
flags = (SzFlag.SzEntityIncludeEntityName |
         SzFlag.SzEntityIncludeRecordData |
         SzFlag.SzEntityIncludeRelatedEntities)
```

### Search Flags

```python
SzFlag.SzSearchByAttributesDefaultFlags
SzFlag.SzSearchIncludeResolved
SzFlag.SzSearchIncludePossiblyRelated
SzFlag.SzSearchIncludeNameOnly
SzFlag.SzSearchIncludeStats
```

### Export Flags

```python
SzFlag.SzExportDefaultFlags
SzFlag.SzExportIncludeMultiRecordEntities
SzFlag.SzExportIncludeSingleRecordEntities
```

### Why/How Flags

```python
SzFlag.SzWhyEntitiesDefaultFlags
SzFlag.SzWhyRecordsDefaultFlags
SzFlag.SzWhyRecordInEntityDefaultFlags
SzFlag.SzWhySearchDefaultFlags
SzFlag.SzHowEntityDefaultFlags
SzFlag.SzIncludeFeatureScores
```

### General Flags

```python
SzFlag.SzNoFlags  # No special handling
SzFlag.SzWithInfo  # Return resolution info (add/delete/reevaluate)
```

## Type Conversions

### Python to .NET

```python
# Strings - direct
engine.AddRecord("SOURCE", "REC123", record_json)

# Integers - direct
entity = engine.GetEntity(12345, flags)

# Booleans - direct
env_builder.VerboseLogging(True)

# JSON - use json.dumps()
record_json = json.dumps({"NAME_FIRST": "John"})

# Collections - use .NET types
from System.Collections.Generic import HashSet, List
from System import Tuple

# HashSet[int]
entity_ids = HashSet[int]()
entity_ids.Add(100)
entity_ids.Add(200)

# HashSet[Tuple[str, str]]
record_keys = HashSet[Tuple[str, str]]()
record_keys.Add(Tuple.Create("CUSTOMERS", "REC001"))

# List[str]
sources = List[str]()
sources.Add("CUSTOMERS")
sources.Add("EMPLOYEES")
```

### .NET to Python

```python
# Strings - direct
result_str = engine.GetEntity(123, flags)
# result_str is Python str

# JSON - use json.loads()
entity = json.loads(result_str)

# Numbers - direct conversion
entity_id = entity["RESOLVED_ENTITY"]["ENTITY_ID"]
# entity_id is Python int

# IntPtr (handles) - pass through, don't modify
handle = engine.ExportJsonEntityReport(flags)
# Use as-is
engine.CloseExport(handle)
```

## Error Handling

### Exception Hierarchy

```python
from Senzing.Sdk import (
    SzException,                      # Base exception
    SzNotFoundException,              # Entity/record not found
    SzUnknownDataSourceException,     # Invalid data source
    SzBadInputException,              # Malformed input
    SzDatabaseException,              # Database errors
    SzDatabaseTransientException,     # Retryable database errors
    SzDatabaseConnectionLostException, # Connection lost
    SzRetryableException,             # Operation can be retried
    SzUnrecoverableException          # Fatal error
)
```

### Error Handling Pattern

```python
try:
    entity_json = engine.GetEntity("CUSTOMERS", "REC123", flags)
    entity = json.loads(entity_json)

except SzNotFoundException as e:
    print(f"Not found: {e}")

except SzUnknownDataSourceException as e:
    print(f"Unknown data source: {e}")

except SzBadInputException as e:
    print(f"Bad input: {e}")

except SzDatabaseTransientException as e:
    # Retry logic
    print(f"Transient error, retrying: {e}")

except SzDatabaseException as e:
    print(f"Database error: {e}")

except SzException as e:
    print(f"Senzing error: {e}")
```

## Resource Management

### Context Manager Pattern

```python
class SzEnvironmentContext:
    def __init__(self, settings_json, instance_name="MyApp"):
        self.settings = settings_json
        self.instance_name = instance_name
        self.env = None

    def __enter__(self):
        self.env = (SzCoreEnvironment.NewBuilder()
                   .InstanceName(self.instance_name)
                   .Settings(self.settings)
                   .Build())
        return self.env

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.env:
            self.env.Destroy()

# Usage
with SzEnvironmentContext(settings_json) as env:
    engine = env.GetEngine()
    # Use engine...
# Automatic cleanup
```

### Manual Cleanup

```python
env = None
try:
    env = (SzCoreEnvironment.NewBuilder()
           .InstanceName("MyApp")
           .Settings(settings_json)
           .Build())

    engine = env.GetEngine()
    # Use engine...

finally:
    if env:
        env.Destroy()
```

## Performance Considerations

### Batch Processing

```python
# Process records in batches
records = [...]  # List of (data_source, record_id, record_data) tuples

for ds, rec_id, rec_data in records:
    try:
        record_json = json.dumps(rec_data)
        engine.AddRecord(ds, rec_id, record_json)
    except SzException as e:
        print(f"Failed to add {ds}:{rec_id}: {e}")
```

### Memory Management

Python.NET handles garbage collection across the language boundary. Always call `env.Destroy()` when finished.

## Complete Example

```python
import clr
import sys
import json

# Configure Python.NET
import os
os.environ["PYTHONNET_PYDLL"] = r"c:\python312\python312.dll"

try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx
    set_runtime(get_netfx())
except:
    pass

# Load assemblies
sys.path.append(r"C:\senzing\sdk\dotnet\lib\netstandard2.0")
clr.AddReference("Senzing.Sdk")

from Senzing.Sdk import SzFlag
from Senzing.Sdk.Core import SzCoreEnvironment

# Initialize
settings = {
    "PIPELINE": {
        "CONFIGPATH": r"C:\senzing\etc",
        "RESOURCEPATH": r"C:\senzing\resources",
        "SUPPORTPATH": r"C:\senzing\data"
    },
    "SQL": {
        "CONNECTION": "sqlite3://na:na@C:\\senzing\\database.db"
    }
}

env = (SzCoreEnvironment.NewBuilder()
       .InstanceName("Example")
       .Settings(json.dumps(settings))
       .Build())

try:
    engine = env.GetEngine()

    # Add record
    record = {"NAME_FIRST": "John", "NAME_LAST": "Doe"}
    info_json = engine.AddRecord(
        "CUSTOMERS",
        "REC001",
        json.dumps(record),
        SzFlag.SzWithInfo
    )

    print(f"Added: {json.loads(info_json)}")

    # Get entity
    flags = (SzFlag.SzEntityIncludeEntityName |
             SzFlag.SzEntityIncludeRecordData)
    entity_json = engine.GetEntity("CUSTOMERS", "REC001", flags)
    entity = json.loads(entity_json)

    print(f"Entity ID: {entity['RESOLVED_ENTITY']['ENTITY_ID']}")

finally:
    env.Destroy()
```

## Additional Resources

- **Senzing C# SDK Documentation**: Official SDK documentation
- **Python.NET Documentation**: https://pythonnet.github.io/
- **Senzing Documentation**: https://docs.senzing.com/

## License

This guide and example code are licensed under Apache 2.0. The Senzing C# SDK is proprietary software - refer to your Senzing license agreement.
