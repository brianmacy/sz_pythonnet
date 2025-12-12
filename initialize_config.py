#!/usr/bin/env python3
"""
Initialize Senzing database with default configuration
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

# Configure pythonnet before importing clr
os.environ["PYTHONNET_PYDLL"] = CONFIG["python"]["dll_path"]

# Configure for .NET Framework (x64) instead of .NET Core
try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx

    # Use .NET Framework runtime (x64)
    rt = get_netfx("v4.0.30319")
    set_runtime(rt)
    print("✓ Using .NET Framework x64 runtime")
except Exception as e:
    print(f"Note: Using default runtime: {e}")

import clr

# Calculate all paths from Senzing root
senzing_root = Path(CONFIG["senzing"]["senzing_root"])
dotnet_sdk_path = str(senzing_root / "er" / "sdk" / "dotnet" / "extracted" / "lib" / "netstandard2.0")
database_path = str(senzing_root / "er" / "var" / "sqldb" / "G2C.db")
config_path = str(senzing_root / "er" / "etc")
resource_path = str(senzing_root / "er" / "resources")
support_path = str(senzing_root / "data")
config_file_path = senzing_root / "er" / "etc" / "g2config.json"

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

print("\nInitializing Senzing database configuration...")
print("=" * 80)

try:
    # Add SDK path to Python path
    sys.path.append(dotnet_sdk_path)

    # Load .NET assemblies
    clr.AddReference("Senzing.Sdk")

    # Import .NET types
    from Senzing.Sdk.Core import SzCoreEnvironment

    # Initialize environment
    settings_json = json.dumps(settings)
    print(f"\nSettings:\n{json.dumps(settings, indent=2)}\n")

    env = (SzCoreEnvironment.NewBuilder()
           .InstanceName("ConfigInit")
           .Settings(settings_json)
           .VerboseLogging(False)
           .Build())

    print("✓ Senzing environment initialized")

    # Get ConfigManager service
    config_mgr = env.GetConfigManager()
    print("✓ Got ConfigManager service")

    # Check if configuration already exists
    try:
        existing_config_id = config_mgr.GetDefaultConfigID()
        print(f"\nFound existing configuration with ID: {existing_config_id}")

        # ID 0 is often invalid/placeholder, so we need to register a real one
        if existing_config_id > 0:
            print("✓ Valid configuration already exists. No action needed.")
            env.Destroy()
            sys.exit(0)
        else:
            print("✓ Config ID 0 is invalid - will create new configuration")

    except Exception:
        # No configuration exists - this is expected
        print("✓ No existing configuration found - will create new one")

    # Read the default configuration template
    print("\nLoading configuration template...")

    try:
        with open(config_file_path, 'r') as f:
            config_json = f.read()
        print(f"✓ Loaded configuration template from {config_file_path}")
        print(f"  Size: {len(config_json)} bytes")
    except Exception as e:
        print(f"✗ Failed to read configuration file: {e}")
        env.Destroy()
        sys.exit(1)

    # Use ConfigManager to create and register the configuration
    print("\nRegistering configuration...")

    try:
        # RegisterConfig takes the config JSON and a comment
        config_id = config_mgr.RegisterConfig(
            config_json,
            "Initial configuration - Python.NET setup"
        )
        print(f"✓ Registered configuration with ID: {config_id}")

    except Exception as e:
        print(f"✗ Failed to register configuration: {e}")
        env.Destroy()
        sys.exit(1)

    # Set as default configuration
    print("\nSetting as default configuration...")

    try:
        config_mgr.SetDefaultConfigID(config_id)
        print(f"✓ Set configuration {config_id} as default")

    except Exception as e:
        print(f"✗ Failed to set default configuration: {e}")
        env.Destroy()
        sys.exit(1)

    # Verify the configuration
    print("\nVerifying configuration...")

    try:
        default_id = config_mgr.GetDefaultConfigID()
        print(f"✓ Verified default configuration ID: {default_id}")

        if default_id == config_id:
            print("✓ Configuration successfully initialized!")
        else:
            print(f"⚠ Warning: Default ID ({default_id}) doesn't match created ID ({config_id})")

    except Exception as e:
        print(f"✗ Failed to verify configuration: {e}")

    # Clean up
    env.Destroy()
    print("\n✓ Environment destroyed")

    print("\n" + "=" * 80)
    print("SUCCESS! Database is now configured and ready to use.")
    print("You can now run example_pythonnet_usage.py")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
