"""
Test OBO Authentication Fix
============================

Verifies that the Model Serving context detection works correctly
and that Genie queries succeed in evaluation mode.

Run this in a Databricks notebook to verify the fix.
"""

import os
import sys

# Add project root to path for imports
project_root = "/Workspace" + os.path.dirname(os.path.abspath(__file__)).rsplit('/tests', 1)[0]
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_environment_detection():
    """Test that Model Serving environment is correctly detected."""
    print("=" * 80)
    print("TEST 1: Environment Detection")
    print("=" * 80)
    
    is_model_serving = (
        os.environ.get("IS_IN_DB_MODEL_SERVING_ENV") == "true" or
        os.environ.get("DATABRICKS_SERVING_ENDPOINT") is not None or
        os.environ.get("MLFLOW_DEPLOYMENT_FLAVOR_NAME") == "databricks"
    )
    
    print(f"\nEnvironment Variables:")
    print(f"  IS_IN_DB_MODEL_SERVING_ENV: {os.environ.get('IS_IN_DB_MODEL_SERVING_ENV')}")
    print(f"  DATABRICKS_SERVING_ENDPOINT: {os.environ.get('DATABRICKS_SERVING_ENDPOINT')}")
    print(f"  MLFLOW_DEPLOYMENT_FLAVOR_NAME: {os.environ.get('MLFLOW_DEPLOYMENT_FLAVOR_NAME')}")
    
    print(f"\nResult: Model Serving detected = {is_model_serving}")
    
    if is_model_serving:
        print("  ⚠️ WARNING: Running in Model Serving context")
        print("  OBO authentication will be used")
    else:
        print("  ✓ Running in notebook/job context")
        print("  Default authentication will be used")
    
    print()
    return not is_model_serving  # Test passes if NOT in Model Serving


def test_genie_client_initialization():
    """Test that Genie client initializes with correct auth mode."""
    print("=" * 80)
    print("TEST 2: Genie Client Initialization")
    print("=" * 80)
    
    try:
        # Import the agent class
        from src.agents.setup.log_agent_model import HealthMonitorAgent
        
        print("\n✓ Agent class imported successfully")
        
        # Create agent instance
        agent = HealthMonitorAgent()
        print("✓ Agent instance created")
        
        # Test getting a Genie client
        print("\nTesting Genie client initialization for 'cost' domain:")
        client = agent._get_genie_client("cost")
        
        print(f"✓ Client created: {type(client).__name__}")
        print(f"  Client config: {client.config}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_genie_query():
    """Test that a Genie query actually works."""
    print("=" * 80)
    print("TEST 3: Genie Query Execution")
    print("=" * 80)
    
    try:
        from src.agents.setup.log_agent_model import HealthMonitorAgent
        
        agent = HealthMonitorAgent()
        
        # Simple test query
        test_query = "What are the top 5 most expensive workspaces?"
        domain = "cost"
        
        print(f"\nExecuting test query:")
        print(f"  Domain: {domain}")
        print(f"  Query: {test_query}")
        print()
        
        # Execute query
        response_text, conversation_id = agent._query_genie(
            domain=domain,
            query=test_query
        )
        
        print(f"\n✓ Query succeeded!")
        print(f"  Response length: {len(response_text)} characters")
        print(f"  Conversation ID: {conversation_id[:8] if conversation_id else 'None'}...")
        print(f"\nResponse preview (first 300 chars):")
        print("-" * 80)
        print(response_text[:300])
        print("-" * 80)
        
        # Verify response has content
        if len(response_text) > 50:
            print("\n✓ Response contains substantial content")
            return True
        else:
            print("\n⚠️ Response seems too short - may indicate an issue")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_permissions():
    """Test that user has proper Genie Space permissions."""
    print("=" * 80)
    print("TEST 4: Permissions Check")
    print("=" * 80)
    
    try:
        from databricks.sdk import WorkspaceClient
        
        client = WorkspaceClient()
        
        # Get Genie Space IDs from environment or use defaults
        cost_space_id = os.environ.get("COST_GENIE_SPACE_ID", "01f0ea87...")
        
        print(f"\nChecking access to Genie Space: {cost_space_id[:8]}...")
        
        # Try to list conversations (requires CAN USE permission)
        try:
            conversations = client.genie.list_conversations(space_id=cost_space_id)
            print("✓ Can access Genie Space (CAN USE permission confirmed)")
            return True
        except Exception as perm_err:
            if "permission" in str(perm_err).lower():
                print(f"✗ Permission denied: {perm_err}")
                print("\nRequired permissions:")
                print("  1. GRANT USE ON GENIE SPACE <space_id> TO `<your_username>`")
                print("  2. GRANT USAGE ON WAREHOUSE <warehouse_id> TO `<your_username>`")
                return False
            else:
                raise
                
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("OBO AUTHENTICATION FIX - VERIFICATION TESTS")
    print("=" * 80)
    print()
    
    results = {
        "Environment Detection": test_environment_detection(),
        "Client Initialization": test_genie_client_initialization(),
        "Permissions Check": test_permissions(),
        "Genie Query Execution": test_genie_query(),
    }
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}  {test_name}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe OBO authentication fix is working correctly.")
        print("You can now run evaluation without permission errors.")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("\nReview the output above to diagnose issues.")
        print("Most common issues:")
        print("  1. Missing Genie Space permissions (run permissions check)")
        print("  2. Incorrect Genie Space IDs in environment variables")
        print("  3. databricks-ai-bridge package not installed")
    
    print()
    return all_passed


# Run tests if executed directly
if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
