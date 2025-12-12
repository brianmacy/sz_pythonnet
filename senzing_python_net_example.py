#!/usr/bin/env python3
"""
Senzing C# SDK via Python.NET - Example

This example demonstrates using the Senzing C# SDK from Python on Windows
using Python.NET (pythonnet). This pattern enables Python applications on
Windows x64 systems to leverage the Senzing C# SDK.

Requirements:
- Python 3.11, 3.12, or 3.13 (x64)
- pythonnet: pip install pythonnet
- .NET Framework 4.x (included with Windows)
- Senzing SDK 4.x for Windows

Note: Customers should test thoroughly in their specific environment.

Author: Senzing
Date: December 2025
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# ============================================================================
# STEP 1: Load Configuration
# ============================================================================


def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_path = Path(__file__).parent / config_file

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please copy config.json.example to config.json and update the paths."
        )

    with open(config_path, 'r') as f:
        return json.load(f)


# Load configuration
CONFIG = load_config()


# ============================================================================
# STEP 2: Configure Python.NET Runtime
# ============================================================================

# Set the Python DLL path from config
os.environ["PYTHONNET_PYDLL"] = CONFIG["python"]["dll_path"]

# Configure for .NET Framework (x64)
try:
    from pythonnet import set_runtime
    from clr_loader import get_netfx
    runtime = get_netfx()
    set_runtime(runtime)
except Exception:
    # Default runtime will be used
    pass

# Import CLR after runtime configuration
import clr


# ============================================================================
# STEP 3: Senzing Client Class
# ============================================================================

class SenzingClient:
    """
    Client for interacting with Senzing entity resolution engine via C# SDK.

    This class provides a simplified interface to common Senzing operations.
    """

    def __init__(self, sdk_path: str, settings: Dict[str, Any]):
        """
        Initialize the Senzing client.

        Args:
            sdk_path: Path to Senzing C# SDK DLL directory
            settings: Configuration settings (database, paths, etc.)
        """
        # Add SDK path and load assemblies
        sys.path.append(sdk_path)
        clr.AddReference("Senzing.Sdk")

        # Import .NET types
        from Senzing.Sdk.Core import SzCoreEnvironment
        from Senzing.Sdk import SzFlag

        # Store types
        self.SzFlag = SzFlag

        # Build environment
        settings_json = json.dumps(settings)
        self.env = (SzCoreEnvironment.NewBuilder()
                    .InstanceName("PythonNetClient")
                    .Settings(settings_json)
                    .VerboseLogging(False)
                    .Build())

        # Get services
        self.engine = self.env.GetEngine()
        self.config_mgr = self.env.GetConfigManager()
        self.product = self.env.GetProduct()

        print("✓ Senzing client initialized successfully")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'env') and self.env is not None:
            self.env.Destroy()

    # ========================================================================
    # Product Information
    # ========================================================================

    def get_version(self) -> Dict[str, Any]:
        """Get Senzing product version information"""
        version_json = self.product.GetVersion()
        return json.loads(version_json)

    def get_license(self) -> Dict[str, Any]:
        """Get Senzing license information"""
        license_json = self.product.GetLicense()
        return json.loads(license_json)

    # ========================================================================
    # Record Operations
    # ========================================================================

    def add_record(self, data_source: str, record_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a record to the Senzing repository.

        Args:
            data_source: Data source code (e.g., "CUSTOMERS")
            record_id: Unique record identifier
            record_data: Record attributes (NAME_FIRST, NAME_LAST, etc.)

        Returns:
            Information about affected entities
        """
        record_json = json.dumps(record_data)
        info_json = self.engine.AddRecord(
            data_source,
            record_id,
            record_json,
            self.SzFlag.SzWithInfo
        )
        return json.loads(info_json)

    def delete_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """
        Delete a record from the Senzing repository.

        Args:
            data_source: Data source code
            record_id: Record identifier to delete

        Returns:
            Information about affected entities
        """
        info_json = self.engine.DeleteRecord(
            data_source,
            record_id,
            self.SzFlag.SzWithInfo
        )
        return json.loads(info_json)

    # ========================================================================
    # Entity Retrieval
    # ========================================================================

    def get_entity_by_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """
        Retrieve an entity by record key.

        Args:
            data_source: Data source code
            record_id: Record identifier

        Returns:
            Entity information including all records
        """
        # Combine flags for comprehensive entity view
        flags = (self.SzFlag.SzEntityIncludeEntityName
                 | self.SzFlag.SzEntityIncludeRecordSummary
                 | self.SzFlag.SzEntityIncludeRecordData)

        entity_json = self.engine.GetEntity(data_source, record_id, flags)
        return json.loads(entity_json)

    def get_entity_by_id(self, entity_id: int) -> Dict[str, Any]:
        """
        Retrieve an entity by entity ID.

        Args:
            entity_id: Senzing entity identifier

        Returns:
            Entity information
        """
        flags = (self.SzFlag.SzEntityIncludeEntityName
                 | self.SzFlag.SzEntityIncludeRecordSummary
                 | self.SzFlag.SzEntityIncludeRecordData)

        entity_json = self.engine.GetEntity(entity_id, flags)
        return json.loads(entity_json)

    # ========================================================================
    # Search Operations
    # ========================================================================

    def search_by_attributes(self, attributes: Dict[str, str]) -> Dict[str, Any]:
        """
        Search for entities matching specified attributes.

        Args:
            attributes: Search criteria (e.g., {"NAME_FIRST": "John", "NAME_LAST": "Doe"})

        Returns:
            Search results with matching entities
        """
        search_json = json.dumps(attributes)

        # Include resolved entities and feature scores
        flags = (self.SzFlag.SzSearchIncludeResolved
                 | self.SzFlag.SzIncludeFeatureScores)

        results_json = self.engine.SearchByAttributes(search_json, flags)
        return json.loads(results_json)

    def get_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """
        Get a specific record.

        Args:
            data_source: Data source code
            record_id: Record identifier

        Returns:
            Record information
        """
        flags = self.SzFlag.SzEntityIncludeRecordData

        record_json = self.engine.GetRecord(data_source, record_id, flags)
        return json.loads(record_json)

    def reevaluate_record(self, data_source: str, record_id: str) -> Dict[str, Any]:
        """
        Reevaluate a record (useful after configuration changes).

        Args:
            data_source: Data source code
            record_id: Record identifier

        Returns:
            Information about affected entities
        """
        info_json = self.engine.ReevaluateRecord(
            data_source,
            record_id,
            self.SzFlag.SzWithInfo
        )
        return json.loads(info_json)

    # ========================================================================
    # Explainability
    # ========================================================================

    def why_entities(self, entity_id1: int, entity_id2: int) -> Dict[str, Any]:
        """
        Explain why two entities resolved or did not resolve together.

        Args:
            entity_id1: First entity ID
            entity_id2: Second entity ID

        Returns:
            Explanation of entity relationship
        """
        flags = self.SzFlag.SzIncludeFeatureScores

        why_json = self.engine.WhyEntities(entity_id1, entity_id2, flags)
        return json.loads(why_json)

    def how_entity(self, entity_id: int) -> Dict[str, Any]:
        """
        Explain how an entity was constructed from its records.

        Args:
            entity_id: Entity identifier

        Returns:
            Step-by-step resolution explanation
        """
        flags = self.SzFlag.SzIncludeFeatureScores

        how_json = self.engine.HowEntity(entity_id, flags)
        return json.loads(how_json)

    # ========================================================================
    # Export Operations
    # ========================================================================

    def export_json_entities(self, max_entities: int = None):
        """
        Export entities as JSON (iterator).

        Args:
            max_entities: Maximum number of entities to export (None for all)

        Yields:
            Entity JSON dictionaries
        """
        flags = (self.SzFlag.SzExportIncludeMultiRecordEntities
                 | self.SzFlag.SzExportIncludeSingleRecordEntities)

        export_handle = self.engine.ExportJsonEntityReport(flags)

        try:
            count = 0
            json_data = self.engine.FetchNext(export_handle)

            while json_data is not None:
                if max_entities and count >= max_entities:
                    break

                yield json.loads(json_data)
                count += 1
                json_data = self.engine.FetchNext(export_handle)

        finally:
            self.engine.CloseExport(export_handle)

    def count_redo_records(self) -> int:
        """Get count of pending redo records"""
        return self.engine.CountRedoRecords()

    def process_redo_records(self, max_records: int = 10):
        """
        Process pending redo records (iterator).

        Args:
            max_records: Maximum number to process

        Yields:
            Result dictionaries with affected entities
        """
        processed = 0
        redo_record = self.engine.GetRedoRecord()

        while redo_record is not None and processed < max_records:
            info_json = self.engine.ProcessRedoRecord(
                redo_record,
                self.SzFlag.SzWithInfo
            )
            yield json.loads(info_json)
            processed += 1
            redo_record = self.engine.GetRedoRecord()


# ============================================================================
# STEP 4: Example Usage
# ============================================================================

def main():
    """Demonstrate Senzing C# SDK usage from Python"""

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

    print("=" * 80)
    print("Senzing C# SDK via Python.NET - Example")
    print("=" * 80)
    print()

    try:
        with SenzingClient(dotnet_sdk_path, settings) as client:

            # Get product information
            version = client.get_version()
            print(f"Senzing Version: {version.get('VERSION', 'Unknown')}")
            print(f"Build: {version.get('BUILD_VERSION', 'Unknown')}")
            print()

            # Example: Add records
            print("Adding sample records...")

            record1 = {
                "NAME_FIRST": "John",
                "NAME_LAST": "Doe",
                "PHONE_NUMBER": "702-555-1212",
                "EMAIL_ADDRESS": "johndoe@example.com",
                "ADDR_FULL": "123 Main St, Las Vegas, NV 89101"
            }

            result1 = client.add_record("CUSTOMERS", "CUST001", record1)
            print("✓ Added CUSTOMERS:CUST001")
            print("  Response JSON:")
            print(json.dumps(result1, indent=2))
            print()

            record2 = {
                "NAME_FIRST": "Jane",
                "NAME_LAST": "Smith",
                "PHONE_NUMBER": "702-555-1313",
                "EMAIL_ADDRESS": "janesmith@example.com"
            }

            result2 = client.add_record("CUSTOMERS", "CUST002", record2)
            print("✓ Added CUSTOMERS:CUST002")
            print("  Response JSON:")
            print(json.dumps(result2, indent=2))
            print()

            # Add a few more records
            record3 = {
                "NAME_FIRST": "Robert",
                "NAME_LAST": "Johnson",
                "PHONE_NUMBER": "702-555-1414",
                "EMAIL_ADDRESS": "robertj@example.com"
            }
            result3 = client.add_record("CUSTOMERS", "CUST003", record3)
            print("✓ Added CUSTOMERS:CUST003")
            print("  Response JSON:")
            print(json.dumps(result3, indent=2))
            print()

            # Add one from EMPLOYEES data source
            record4 = {
                "NAME_FIRST": "John",
                "NAME_LAST": "Doe",
                "PHONE_NUMBER": "702-555-1212",
                "DATE_OF_BIRTH": "1980-05-15"
            }
            result4 = client.add_record("EMPLOYEES", "EMP001", record4)
            print("✓ Added EMPLOYEES:EMP001")
            print("  Response JSON:")
            print(json.dumps(result4, indent=2))
            print()

            # Example: Retrieve entity
            print("Retrieving entity...")
            entity = client.get_entity_by_record("CUSTOMERS", "CUST001")

            print("✓ Entity retrieved:")
            print(json.dumps(entity, indent=2))
            print()

            # Example: Search
            print("Searching for entities...")
            search_criteria = {
                "NAME_FIRST": "John",
                "NAME_LAST": "Doe"
            }

            search_results = client.search_by_attributes(search_criteria)

            print("✓ Search results:")
            print(json.dumps(search_results, indent=2))
            print()

            # Example: Get Record
            print("Getting specific record...")
            record_data = client.get_record("CUSTOMERS", "CUST001")
            print("✓ Record data:")
            print(json.dumps(record_data, indent=2))
            print()

            # Example: Why analysis (if records resolved together)
            print("Why analysis (comparing two entities)...")
            try:
                # Get entity IDs from our records
                entity1 = client.get_entity_by_record("CUSTOMERS", "CUST001")
                entity1_id = entity1["RESOLVED_ENTITY"]["ENTITY_ID"]

                entity2 = client.get_entity_by_record("EMPLOYEES", "EMP001")
                entity2_id = entity2["RESOLVED_ENTITY"]["ENTITY_ID"]

                if entity1_id != entity2_id:
                    why_results = client.why_entities(entity1_id, entity2_id)
                    print(f"✓ Why entities {entity1_id} vs {entity2_id}:")
                    print(json.dumps(why_results, indent=2))
                else:
                    print(f"✓ Entities resolved together as entity {entity1_id}")
                    # Show how they resolved
                    how_results = client.how_entity(entity1_id)
                    print(f"✓ How entity {entity1_id} was constructed:")
                    print(json.dumps(how_results, indent=2))
            except Exception as e:
                print(f"  (Why/How analysis: {e})")
            print()

            # Example: Delete a record
            print("Deleting a record...")
            delete_result = client.delete_record("CUSTOMERS", "CUST002")
            print("✓ Deleted CUSTOMERS:CUST002")
            print("  Response JSON:")
            print(json.dumps(delete_result, indent=2))
            print()

            print("=" * 80)
            print("Example completed successfully!")
            print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
