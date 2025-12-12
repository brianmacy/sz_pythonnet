#!/usr/bin/env python3
"""
Add CUSTOMERS and EMPLOYEES data sources to Senzing configuration
"""

import os
import sys
import json
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please copy config.json.example to config.json and update the paths."
        )
    with open(config_path, 'r') as f:
        return json.load(f)


CONFIG = load_config()

os.environ["PYTHONNET_PYDLL"] = CONFIG["python"]["dll_path"]

try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx
    rt = get_netfx()
    set_runtime(rt)
except Exception:
    pass

import clr

# Calculate all paths from Senzing root
senzing_root = Path(CONFIG["senzing"]["senzing_root"])
dotnet_sdk_path = str(senzing_root / "er" / "sdk" / "dotnet" / "extracted" / "lib" / "netstandard2.0")
database_path = str(senzing_root / "er" / "var" / "sqldb" / "G2C.db")
config_path = str(senzing_root / "er" / "etc")
resource_path = str(senzing_root / "er" / "resources")
support_path = str(senzing_root / "data")

settings = {
    "PIPELINE": {
        "CONFIGPATH": config_path,
        "RESOURCEPATH": resource_path,
        "SUPPORTPATH": support_path
    },
    "SQL": {
        "CONNECTION": f"sqlite3://na:na@{database_path}"
    }
}

print("Adding data sources to Senzing configuration...")
print("=" * 80)

try:
    sys.path.append(dotnet_sdk_path)
    clr.AddReference("Senzing.Sdk")

    from Senzing.Sdk.Core import SzCoreEnvironment

    settings_json = json.dumps(settings)

    env = (SzCoreEnvironment.NewBuilder()
           .InstanceName("AddDataSources")
           .Settings(settings_json)
           .VerboseLogging(False)
           .Build())

    print("✓ Environment initialized")

    config_mgr = env.GetConfigManager()
    print("✓ Got ConfigManager service")

    # Get current default config ID
    current_config_id = config_mgr.GetDefaultConfigID()
    print(f"\nCurrent config ID: {current_config_id}")

    # Create a config object from the current config
    config = config_mgr.CreateConfig(current_config_id)
    print("✓ Created config object from current configuration")

    # Get current data sources to check what exists
    data_source_registry_json = config.GetDataSourceRegistry()
    data_source_registry = json.loads(data_source_registry_json)
    existing_ds = {ds["DSRC_CODE"] for ds in data_source_registry.get("DATA_SOURCES", [])}

    print(f"\nExisting data sources: {existing_ds}")

    # Determine what data sources to add
    data_sources_to_add = []
    for ds_code in ["CUSTOMERS", "EMPLOYEES"]:
        if ds_code not in existing_ds:
            data_sources_to_add.append(ds_code)

    if not data_sources_to_add:
        print("✓ CUSTOMERS and EMPLOYEES data sources already exist")
        env.Destroy()
        sys.exit(0)

    print(f"\nAdding data sources: {data_sources_to_add}")

    # Add each data source
    for ds_code in data_sources_to_add:
        try:
            config.RegisterDataSource(ds_code)
            print(f"✓ Registered data source: {ds_code}")
        except Exception as e:
            print(f"✗ Failed to add {ds_code}: {e}")

    # Export the modified configuration
    new_config_json = config.Export()
    print("✓ Exported modified configuration")

    # Register the new configuration
    new_config_id = config_mgr.RegisterConfig(
        new_config_json,
        f"Added data sources: {', '.join(data_sources_to_add)}"
    )
    print(f"✓ Registered new configuration with ID: {new_config_id}")

    # Replace the default configuration (handles race conditions)
    config_mgr.ReplaceDefaultConfigID(current_config_id, new_config_id)
    print(f"✓ Replaced default config (old: {current_config_id}, new: {new_config_id})")

    # Verify
    verify_id = config_mgr.GetDefaultConfigID()
    print(f"✓ Verified default config ID: {verify_id}")

    env.Destroy()

    print("\n" + "=" * 80)
    print("SUCCESS! Data sources added successfully.")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
