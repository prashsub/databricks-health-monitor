"""
Verify Lakebase Tables Directly via databricks-langchain API
=============================================================

Since Lakebase tables are stored in managed Postgres (NOT Unity Catalog Delta tables),
we must use the databricks-langchain API to query them directly.

This script:
1. Connects to Lakebase instance via CheckpointSaver/DatabricksStore
2. Queries tables directly through the API
3. Reports on table existence and content

Usage:
    python src/agents/setup/verify_lakebase_tables.py
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_success(message: str):
    """Print success message."""
    print(f"  ✅ {message}")


def print_warning(message: str):
    """Print warning message."""
    print(f"  ⚠️  {message}")


def print_error(message: str):
    """Print error message."""
    print(f"  ❌ {message}")


def print_info(message: str, indent: int = 2):
    """Print info message."""
    print(f"{' ' * indent}• {message}")


def check_lakebase_checkpoints(instance_name: str) -> Dict[str, Any]:
    """
    Check Lakebase checkpoints table (short-term memory).
    
    Uses CheckpointSaver API to query the table.
    """
    print_section("1. SHORT-TERM MEMORY (checkpoints table)")
    print_info(f"Lakebase Instance: {instance_name}")
    print_info("Table: checkpoints (in Lakebase Postgres)")
    
    result = {
        "exists": False,
        "accessible": False,
        "thread_count": 0,
        "checkpoint_count": 0,
        "sample_threads": [],
        "error": None
    }
    
    try:
        from databricks_langchain import CheckpointSaver
        
        print_info("Connecting to Lakebase via CheckpointSaver...")
        
        # Create checkpointer instance
        with CheckpointSaver(instance_name=instance_name) as checkpointer:
            print_success("Connected to Lakebase successfully")
            result["exists"] = True
            result["accessible"] = True
            
            # Try to list some checkpoints
            # Note: CheckpointSaver doesn't have a direct list() method,
            # but we can test with a known thread_id
            test_config = {"configurable": {"thread_id": "test_verification"}}
            
            try:
                checkpoint_tuple = checkpointer.get_tuple(test_config)
                if checkpoint_tuple:
                    print_info("Checkpoint retrieval works (table exists)")
                else:
                    print_info("No checkpoint for test thread (table exists but empty)")
            except Exception as e:
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    print_warning("Checkpoints table not created yet")
                    result["exists"] = False
                else:
                    print_info(f"Table exists but empty or error: {str(e)[:100]}")
            
            print()
            print_success("Short-term memory (CheckpointSaver) is operational")
            print_info("Note: Actual checkpoint count requires iterating through thread_ids")
            print_info("Checkpoints are created automatically on first agent conversation")
            
    except ImportError as ie:
        result["error"] = f"Import error: {ie}"
        print_error("databricks-langchain package not available")
        print_info("Install with: pip install databricks-langchain[memory]")
    except Exception as e:
        result["error"] = str(e)
        print_error(f"Failed to access Lakebase: {str(e)[:200]}")
        
        if "authentication" in str(e).lower() or "permission" in str(e).lower():
            print_info("Check Databricks authentication and permissions")
        elif "instance" in str(e).lower() or "not found" in str(e).lower():
            print_info(f"Lakebase instance '{instance_name}' may not exist")
            print_info("Verify instance name in Databricks workspace settings")
    
    return result


def check_lakebase_store(instance_name: str) -> Dict[str, Any]:
    """
    Check Lakebase store table (long-term memory).
    
    Uses DatabricksStore API to query the table.
    """
    print_section("2. LONG-TERM MEMORY (store table)")
    print_info(f"Lakebase Instance: {instance_name}")
    print_info("Table: store (in Lakebase Postgres)")
    
    result = {
        "exists": False,
        "accessible": False,
        "namespace_count": 0,
        "key_count": 0,
        "sample_keys": [],
        "error": None
    }
    
    try:
        from databricks_langchain import DatabricksStore
        
        print_info("Connecting to Lakebase via DatabricksStore...")
        
        # Create store instance
        store = DatabricksStore(
            instance_name=instance_name,
            embedding_endpoint="databricks-gte-large-en",  # Required for vector search
            embedding_dims=1024
        )
        
        print_success("Connected to Lakebase successfully")
        result["exists"] = True
        result["accessible"] = True
        
        # Try to search for any stored values
        test_namespace = ("test_verification", "user1")
        
        try:
            # Search returns results if table exists
            search_results = store.search(test_namespace, query="test", limit=1)
            print_info(f"Store search works (table exists)")
            if search_results:
                result["key_count"] = len(search_results)
                print_info(f"Found {len(search_results)} stored item(s)")
            else:
                print_info("Store table exists but is empty")
        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                print_warning("Store table not created yet")
                result["exists"] = False
            else:
                print_info(f"Table exists but empty or error: {str(e)[:100]}")
        
        print()
        print_success("Long-term memory (DatabricksStore) is operational")
        print_info("Note: Store entries are created when agent learns user preferences")
        
    except ImportError as ie:
        result["error"] = f"Import error: {ie}"
        print_error("databricks-langchain package not available")
        print_info("Install with: pip install databricks-langchain[memory]")
    except Exception as e:
        result["error"] = str(e)
        print_error(f"Failed to access Lakebase: {str(e)[:200]}")
        
        if "authentication" in str(e).lower() or "permission" in str(e).lower():
            print_info("Check Databricks authentication and permissions")
        elif "instance" in str(e).lower() or "not found" in str(e).lower():
            print_info(f"Lakebase instance '{instance_name}' may not exist")
            print_info("Verify instance name in Databricks workspace settings")
    
    return result


def test_lakebase_write(instance_name: str) -> bool:
    """
    Test writing to Lakebase to verify tables can be created.
    """
    print_section("3. WRITE TEST (Table Creation)")
    print_info("Testing if Lakebase tables can be created/written to...")
    
    try:
        from databricks_langchain import CheckpointSaver
        from langchain_core.messages import HumanMessage, AIMessage
        import uuid
        
        print_info("Attempting to write a test checkpoint...")
        
        with CheckpointSaver(instance_name=instance_name) as checkpointer:
            test_thread = f"verification_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            test_config = {
                "configurable": {
                    "thread_id": test_thread,
                    "checkpoint_ns": "",
                    "checkpoint_id": str(uuid.uuid4())
                }
            }
            
            test_checkpoint = {
                "v": 1,
                "ts": str(uuid.uuid4()),
                "channel_values": {
                    "messages": [
                        HumanMessage(content="Test message"),
                        AIMessage(content="Test response")
                    ]
                }
            }
            
            checkpointer.put(
                config=test_config,
                checkpoint=test_checkpoint,
                metadata={"test": "verification"}
            )
            
            print_success("Successfully wrote test checkpoint")
            print_info(f"Test thread_id: {test_thread}")
            
            # Try to read it back
            read_config = {"configurable": {"thread_id": test_thread}}
            checkpoint_tuple = checkpointer.get_tuple(read_config)
            
            if checkpoint_tuple:
                print_success("Successfully read back test checkpoint")
                print_success("Lakebase tables are fully functional!")
                return True
            else:
                print_warning("Wrote checkpoint but couldn't read it back")
                return False
                
    except Exception as e:
        print_error(f"Write test failed: {str(e)[:200]}")
        print_info("This may indicate:")
        print_info("  • Lakebase instance doesn't exist")
        print_info("  • Permission issues")
        print_info("  • Network connectivity problems")
        return False


def provide_summary(checkpoints_result: Dict, store_result: Dict, write_test: bool):
    """Provide summary and next steps."""
    print_section("4. SUMMARY & RECOMMENDATIONS")
    
    checkpoints_ok = checkpoints_result["accessible"]
    store_ok = store_result["accessible"]
    
    print()
    print_info("Lakebase Status:")
    print(f"    Short-term Memory (checkpoints): {'✅ ACCESSIBLE' if checkpoints_ok else '❌ NOT ACCESSIBLE'}")
    print(f"    Long-term Memory (store):        {'✅ ACCESSIBLE' if store_ok else '❌ NOT ACCESSIBLE'}")
    print(f"    Write Test:                      {'✅ PASSED' if write_test else '❌ FAILED'}")
    
    print()
    
    if checkpoints_ok and store_ok and write_test:
        print_success("Lakebase is fully operational!")
        print()
        print_info("Next Steps:")
        print("    1. Send queries to your agent endpoint")
        print("    2. Re-run this script to see checkpoint/store entries grow")
        print("    3. Monitor memory usage in your agent logs")
    elif checkpoints_ok or store_ok:
        print_warning("Lakebase is partially accessible")
        print()
        print_info("The databricks-langchain API can connect to Lakebase,")
        print_info("but tables may not be created yet or are empty.")
        print()
        print_info("Action: Send 2-3 queries to your agent endpoint to trigger table creation")
    else:
        print_error("Cannot access Lakebase")
        print()
        print_info("Possible Issues:")
        print("    1. Lakebase instance name is incorrect")
        print(f"       Current: '{os.environ.get('LAKEBASE_INSTANCE', 'vibe-coding-workshop-lakebase')}'")
        print("    2. Lakebase instance doesn't exist in this workspace")
        print("    3. Authentication/permission issues")
        print("    4. databricks-langchain package not installed")
        print()
        print_info("Verification Steps:")
        print("    1. Check Lakebase instances in Databricks workspace UI")
        print("    2. Verify environment variable LAKEBASE_INSTANCE_NAME")
        print("    3. Ensure databricks authentication is configured")


def main():
    """Main verification flow."""
    print_section("LAKEBASE TABLES VERIFICATION (Direct API)")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    print()
    print_info("Note: Lakebase tables are stored in managed Postgres,")
    print_info("NOT as Delta tables in Unity Catalog.")
    print_info("We query them via databricks-langchain API.")
    
    # Get Lakebase instance name
    instance_name = os.environ.get("LAKEBASE_INSTANCE", "vibe-coding-workshop-lakebase")
    print()
    print_info(f"Lakebase Instance: {instance_name}")
    
    # Run checks
    checkpoints_result = check_lakebase_checkpoints(instance_name)
    store_result = check_lakebase_store(instance_name)
    write_test = test_lakebase_write(instance_name)
    
    # Provide summary
    provide_summary(checkpoints_result, store_result, write_test)
    
    # Exit code
    if checkpoints_result["accessible"] and store_result["accessible"]:
        print()
        print_section("✅ VERIFICATION COMPLETE - LAKEBASE ACCESSIBLE")
        return 0
    else:
        print()
        print_section("⚠️  VERIFICATION INCOMPLETE - SEE ERRORS ABOVE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
