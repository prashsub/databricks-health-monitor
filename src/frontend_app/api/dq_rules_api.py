"""
DQ Rules Management API

REST endpoints for frontend app to manage DQ rules.
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import uuid

class DQRulesAPI:
    """API for managing DQ rules configuration."""
    
    def __init__(self, workspace_client: WorkspaceClient, catalog: str, schema: str, warehouse_id: str):
        self.client = workspace_client
        self.table_name = f"{catalog}.{schema}.dq_rules"
        self.warehouse_id = warehouse_id
    
    def list_rules(self, table_name: str = None, enabled_only: bool = False):
        """List all DQ rules, optionally filtered."""
        
        where_clauses = []
        if table_name:
            where_clauses.append(f"table_name = '{table_name}'")
        if enabled_only:
            where_clauses.append("enabled = true")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            rule_id,
            table_name,
            rule_name,
            rule_constraint,
            severity,
            enabled,
            description,
            created_by,
            created_at,
            updated_by,
            updated_at
        FROM {self.table_name}
        WHERE {where_clause}
        ORDER BY table_name, severity DESC, rule_name
        """
        
        result = self.client.statement_execution.execute_statement(
            statement=query,
            warehouse_id=self.warehouse_id
        )
        
        return result.result.data_array
    
    def get_rule(self, rule_id: str):
        """Get a specific rule by ID."""
        
        query = f"""
        SELECT * FROM {self.table_name}
        WHERE rule_id = '{rule_id}'
        """
        
        result = self.client.statement_execution.execute_statement(
            statement=query,
            warehouse_id=self.warehouse_id
        )
        
        return result.result.data_array[0] if result.result.data_array else None
    
    def create_rule(self, rule_data: dict, user_email: str):
        """Create a new DQ rule."""
        
        rule_id = str(uuid.uuid4())
        
        insert_sql = f"""
        INSERT INTO {self.table_name} VALUES (
            '{rule_id}',
            '{rule_data["table_name"]}',
            '{rule_data["rule_name"]}',
            '{rule_data["rule_constraint"]}',
            '{rule_data["severity"]}',
            {rule_data.get("enabled", True)},
            '{rule_data.get("description", "")}',
            '{user_email}',
            current_timestamp(),
            '{user_email}',
            current_timestamp()
        )
        """
        
        self.client.statement_execution.execute_statement(
            statement=insert_sql,
            warehouse_id=self.warehouse_id
        )
        
        return rule_id
    
    def update_rule(self, rule_id: str, updates: dict, user_email: str):
        """Update an existing DQ rule."""
        
        set_clauses = []
        for key, value in updates.items():
            if isinstance(value, str):
                set_clauses.append(f"{key} = '{value}'")
            elif isinstance(value, bool):
                set_clauses.append(f"{key} = {value}")
            else:
                set_clauses.append(f"{key} = {value}")
        
        set_clauses.append(f"updated_by = '{user_email}'")
        set_clauses.append("updated_at = current_timestamp()")
        
        update_sql = f"""
        UPDATE {self.table_name}
        SET {', '.join(set_clauses)}
        WHERE rule_id = '{rule_id}'
        """
        
        self.client.statement_execution.execute_statement(
            statement=update_sql,
            warehouse_id=self.warehouse_id
        )
    
    def toggle_rule(self, rule_id: str, enabled: bool, user_email: str):
        """Enable or disable a rule."""
        
        update_sql = f"""
        UPDATE {self.table_name}
        SET 
            enabled = {enabled},
            updated_by = '{user_email}',
            updated_at = current_timestamp()
        WHERE rule_id = '{rule_id}'
        """
        
        self.client.statement_execution.execute_statement(
            statement=update_sql,
            warehouse_id=self.warehouse_id
        )
    
    def delete_rule(self, rule_id: str):
        """Delete a DQ rule (soft delete - set enabled=false recommended)."""
        
        delete_sql = f"""
        DELETE FROM {self.table_name}
        WHERE rule_id = '{rule_id}'
        """
        
        self.client.statement_execution.execute_statement(
            statement=delete_sql,
            warehouse_id=self.warehouse_id
        )
    
    def get_rule_history(self, rule_id: str):
        """Get change history for a rule using Delta CDC."""
        
        history_query = f"""
        SELECT 
            _change_type,
            rule_name,
            rule_constraint,
            severity,
            enabled,
            updated_by,
            updated_at,
            _commit_timestamp
        FROM table_changes('{self.table_name}', 0)
        WHERE rule_id = '{rule_id}'
        ORDER BY _commit_timestamp DESC
        """
        
        result = self.client.statement_execution.execute_statement(
            statement=history_query,
            warehouse_id=self.warehouse_id
        )
        
        return result.result.data_array





