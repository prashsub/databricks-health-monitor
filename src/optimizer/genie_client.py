"""
Genie Space API Client for the Optimizer.

Provides a high-level interface for:
- Asking questions to Genie Spaces
- Managing Genie Space configuration
- Adding instructions and sample queries

Rate Limits:
- 5 POST requests/minute/workspace
- GET requests are unlimited

Usage:
    client = GenieClient(
        workspace_url="https://e2-demo-field-eng.cloud.databricks.com",
        space_id="01f0f1a3c2dc1c8897de11d27ca2cb6f"
    )
    
    response = client.ask_question("What is our total spend?")
    print(response.sql)
    print(response.result_data)
"""

import json
import time
from datetime import datetime
from typing import Any, Optional

import requests

from src.optimizer.models import GenieResponse, ResponseStatus
from src.optimizer.config import OptimizerConfig, load_config, get_space_info


class GenieClient:
    """
    Client for interacting with Genie Space APIs.
    
    Handles:
    - Conversation management (start, poll, get results)
    - Rate limiting (12+ seconds between POST requests)
    - Error handling and retries
    - Space configuration updates
    """
    
    def __init__(
        self,
        workspace_url: Optional[str] = None,
        space_id: Optional[str] = None,
        token: Optional[str] = None,
        config: Optional[OptimizerConfig] = None,
    ):
        """
        Initialize the Genie client.
        
        Args:
            workspace_url: Databricks workspace URL
            space_id: Genie Space ID to interact with
            token: Databricks API token
            config: Optional OptimizerConfig (if not provided, loads from env)
        """
        self.config = config or load_config(workspace_url=workspace_url, token=token)
        self.space_id = space_id
        self._last_post_time: Optional[datetime] = None
        
        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
        })
    
    @property
    def _base_url(self) -> str:
        """Base URL for Genie API."""
        return f"{self.config.workspace_url}/api/2.0/genie/spaces/{self.space_id}"
    
    def _enforce_rate_limit(self):
        """Enforce rate limit between POST requests."""
        if self._last_post_time is not None:
            elapsed = (datetime.now() - self._last_post_time).total_seconds()
            if elapsed < self.config.rate_limit_seconds:
                sleep_time = self.config.rate_limit_seconds - elapsed
                print(f"⏳ Rate limit: waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        self._last_post_time = datetime.now()
    
    def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request with rate limiting."""
        self._enforce_rate_limit()
        
        url = f"{self._base_url}/{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.post(
                    url,
                    json=data,
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⚠️ Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _get(self, endpoint: str) -> dict:
        """Make a GET request (no rate limiting)."""
        url = f"{self._base_url}/{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.get(
                    url,
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ GET failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _patch(self, endpoint: str, data: dict) -> dict:
        """Make a PATCH request with rate limiting."""
        self._enforce_rate_limit()
        
        url = f"{self._base_url}/{endpoint}" if endpoint else self._base_url
        
        response = self._session.patch(
            url,
            json=data,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    
    def ask_question(
        self,
        question: str,
        timeout_seconds: Optional[int] = None,
        verbose: bool = True,
    ) -> GenieResponse:
        """
        Ask a question to the Genie Space and wait for the response.
        
        This is the main method for testing - it:
        1. Starts a conversation
        2. Polls until completion
        3. Retrieves and returns results
        
        Args:
            question: Natural language question to ask
            timeout_seconds: Override timeout for this request
            verbose: Whether to print progress
            
        Returns:
            GenieResponse with SQL, results, and status
        """
        timeout = timeout_seconds or self.config.timeout_seconds
        
        if verbose:
            print(f"\n🤖 Asking: \"{question}\"")
        
        # Step 1: Start conversation
        try:
            start_response = self._post("start-conversation", {"content": question})
        except Exception as e:
            return GenieResponse(
                status=ResponseStatus.FAILED,
                error=f"Failed to start conversation: {str(e)}",
            )
        
        conversation_id = start_response.get("conversation_id")
        message_id = start_response.get("message_id")
        
        if not conversation_id or not message_id:
            return GenieResponse(
                status=ResponseStatus.FAILED,
                error=f"Invalid response: missing conversation_id or message_id",
                raw_response=start_response,
            )
        
        if verbose:
            print(f"   📝 Conversation: {conversation_id[:8]}...")
        
        # Step 2: Poll for completion
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                return GenieResponse(
                    status=ResponseStatus.FAILED,
                    error=f"Timeout after {timeout}s",
                    conversation_id=conversation_id,
                    message_id=message_id,
                )
            
            try:
                message_response = self._get(
                    f"conversations/{conversation_id}/messages/{message_id}"
                )
            except Exception as e:
                return GenieResponse(
                    status=ResponseStatus.FAILED,
                    error=f"Failed to poll message: {str(e)}",
                    conversation_id=conversation_id,
                    message_id=message_id,
                )
            
            status = message_response.get("status", "UNKNOWN")
            
            if status == "COMPLETED":
                break
            elif status == "FAILED":
                error_msg = message_response.get("error", {}).get("message", "Unknown error")
                return GenieResponse(
                    status=ResponseStatus.FAILED,
                    error=error_msg,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    raw_response=message_response,
                )
            elif status in ("IN_PROGRESS", "EXECUTING_QUERY"):
                if verbose:
                    print(f"   ⏳ Status: {status} ({elapsed:.0f}s)")
                time.sleep(self.config.poll_interval_seconds)
            else:
                # Unknown status
                time.sleep(self.config.poll_interval_seconds)
        
        if verbose:
            print(f"   ✅ Completed in {elapsed:.1f}s")
        
        # Step 3: Extract SQL and results from attachments
        attachments = message_response.get("attachments", [])
        sql = None
        result_data = None
        result_columns = None
        attachment_ids = []
        
        for attachment in attachments:
            att_id = attachment.get("attachment_id")
            att_type = attachment.get("attachment_type") or attachment.get("type")
            
            if att_id:
                attachment_ids.append(att_id)
            
            # Extract SQL from query attachment
            if att_type == "QUERY":
                query_info = attachment.get("query", {})
                sql = query_info.get("query") or query_info.get("sql")
                
                # If no SQL in attachment, try to fetch query results
                if att_id and not result_data:
                    try:
                        results = self._get(
                            f"conversations/{conversation_id}/messages/{message_id}/attachments/{att_id}/query-result"
                        )
                        
                        # Extract columns and data
                        statement_response = results.get("statement_response", {})
                        manifest = statement_response.get("manifest", {})
                        result_chunk = statement_response.get("result", {})
                        
                        # Get column names
                        if manifest.get("schema", {}).get("columns"):
                            result_columns = [
                                col.get("name") for col in manifest["schema"]["columns"]
                            ]
                        
                        # Get data
                        data_array = result_chunk.get("data_array", [])
                        if data_array and result_columns:
                            result_data = [
                                dict(zip(result_columns, row))
                                for row in data_array
                            ]
                    except Exception as e:
                        if verbose:
                            print(f"   ⚠️ Could not fetch results: {e}")
            
            # Also check for TEXT attachments (may contain explanations)
            elif att_type == "TEXT":
                text_content = attachment.get("text", {}).get("content", "")
                if verbose and text_content:
                    print(f"   💬 Genie says: {text_content[:100]}...")
        
        return GenieResponse(
            status=ResponseStatus.COMPLETED,
            sql=sql,
            result_data=result_data,
            result_columns=result_columns,
            conversation_id=conversation_id,
            message_id=message_id,
            attachments=attachment_ids,
            raw_response=message_response,
        )
    
    def get_space_config(self) -> dict:
        """
        Get the current Genie Space configuration.
        
        Returns:
            Full space configuration including serialized_space
        """
        response = self._session.get(
            f"{self._base_url}?include_serialized_space=true",
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    
    def add_instruction(self, instruction: str) -> bool:
        """
        Add an instruction to the Genie Space.
        
        ⚠️ Use sparingly! Instructions have a ~4000 character limit total.
        Prefer UC metadata updates instead.
        
        Args:
            instruction: Instruction text to add
            
        Returns:
            True if successful
        """
        print(f"\n📝 Adding instruction: \"{instruction[:50]}...\"")
        
        # Get current config
        config = self.get_space_config()
        serialized = json.loads(config.get("serialized_space", "{}"))
        
        # Add instruction
        instructions = serialized.get("instructions", [])
        instructions.append({
            "content": instruction,
            "created_at": datetime.now().isoformat(),
        })
        serialized["instructions"] = instructions
        
        # Update space
        self._patch("", {"serialized_space": json.dumps(serialized)})
        print("   ✅ Instruction added")
        return True
    
    def add_sample_query(self, question: str, sql: str) -> bool:
        """
        Add a sample query to the Genie Space.
        
        Sample queries help Genie learn the correct SQL patterns.
        
        Args:
            question: Natural language question
            sql: Correct SQL for the question
            
        Returns:
            True if successful
        """
        print(f"\n📝 Adding sample query: \"{question[:50]}...\"")
        
        # Get current config
        config = self.get_space_config()
        serialized = json.loads(config.get("serialized_space", "{}"))
        
        # Add sample query
        sample_queries = serialized.get("sample_queries", [])
        sample_queries.append({
            "question": question,
            "sql": sql,
            "created_at": datetime.now().isoformat(),
        })
        serialized["sample_queries"] = sample_queries
        
        # Update space
        self._patch("", {"serialized_space": json.dumps(serialized)})
        print("   ✅ Sample query added")
        return True
    
    def get_instructions(self) -> list[dict]:
        """Get current instructions from the Genie Space."""
        config = self.get_space_config()
        serialized = json.loads(config.get("serialized_space", "{}"))
        return serialized.get("instructions", [])
    
    def get_sample_queries(self) -> list[dict]:
        """Get current sample queries from the Genie Space."""
        config = self.get_space_config()
        serialized = json.loads(config.get("serialized_space", "{}"))
        return serialized.get("sample_queries", [])
    
    def clear_instructions(self) -> bool:
        """Clear all instructions from the Genie Space."""
        print("\n🗑️ Clearing all instructions...")
        
        config = self.get_space_config()
        serialized = json.loads(config.get("serialized_space", "{}"))
        serialized["instructions"] = []
        
        self._patch("", {"serialized_space": json.dumps(serialized)})
        print("   ✅ Instructions cleared")
        return True


def create_client_for_domain(domain: str) -> GenieClient:
    """
    Create a GenieClient for a specific domain.
    
    Args:
        domain: Domain name (cost, reliability, etc.)
        
    Returns:
        Configured GenieClient
    """
    space_info = get_space_info(domain)
    config = load_config()
    
    return GenieClient(
        config=config,
        space_id=space_info["id"],
    )
