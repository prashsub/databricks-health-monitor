# Databricks notebook source
"""
Health Monitor - Gold Layer Setup (YAML-Driven)

Creates Gold layer tables directly from YAML schema definitions at runtime.
YAML files are the single source of truth - no code generation required.

Usage:
  - Set 'domain' parameter to a specific domain (e.g., 'billing', 'compute')
  - Set 'domain' to 'all' to create tables for all domains

YAML Location: gold_layer_design/yaml/{domain}/*.yaml
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pyspark.sql import SparkSession


# ============================================================================
# CONFIGURATION
# ============================================================================

# Standard table properties for all Gold tables
STANDARD_PROPERTIES = {
    "delta.enableChangeDataFeed": "true",
    "delta.enableRowTracking": "true",
    "delta.enableDeletionVectors": "true",
    "delta.autoOptimize.autoCompact": "true",
    "delta.autoOptimize.optimizeWrite": "true",
    "layer": "gold",
}

# Type normalization mapping
TYPE_MAPPING = {
    "DECIMAL(38": "DECIMAL(38,10)",
    "DECIMAL": "DECIMAL(38,10)",
}


# ============================================================================
# YAML FILE DISCOVERY
# ============================================================================

def find_yaml_base() -> Path:
    """
    Find the YAML base directory.
    Works in both local development and Databricks workspace.
    """
    # In Databricks, files are synced relative to the bundle root
    # The notebook runs from: .bundle/{bundle}/dev/files/src/gold/
    # YAMLs are at: .bundle/{bundle}/dev/files/gold_layer_design/yaml/
    
    possible_paths = [
        # Relative to notebook location in Databricks
        Path("../../gold_layer_design/yaml"),
        # Absolute workspace path (backup)
        Path("/Workspace/Users") / os.environ.get("USER", "unknown") / ".bundle/databricks_health_monitor/dev/files/gold_layer_design/yaml",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Try to resolve from current working directory
    cwd = Path.cwd()
    yaml_path = cwd / "gold_layer_design" / "yaml"
    if yaml_path.exists():
        return yaml_path
    
    # Last resort - look for it in parent directories
    for parent in cwd.parents:
        yaml_path = parent / "gold_layer_design" / "yaml"
        if yaml_path.exists():
            return yaml_path
    
    raise FileNotFoundError(
        "Could not find YAML directory. Tried:\n" + 
        "\n".join([f"  - {p}" for p in possible_paths])
    )


def get_all_domains(yaml_base: Path) -> List[str]:
    """Get all domain directory names."""
    return sorted([d.name for d in yaml_base.iterdir() if d.is_dir()])


def get_domain_yamls(yaml_base: Path, domain: str) -> List[Path]:
    """Get all YAML files for a specific domain."""
    domain_path = yaml_base / domain
    if not domain_path.exists():
        return []
    return sorted(domain_path.glob("*.yaml"))


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ============================================================================
# DDL GENERATION
# ============================================================================

def escape_sql_string(s: str) -> str:
    """Escape single quotes for SQL strings."""
    if not s:
        return ""
    return s.replace("'", "''")


def normalize_type(col_type: str) -> str:
    """Normalize column type from YAML to valid SQL type."""
    col_type = col_type.upper().strip()
    
    # Handle known mappings
    for pattern, replacement in TYPE_MAPPING.items():
        if col_type.startswith(pattern):
            return replacement
    
    return col_type


def build_column_ddl(col: Dict[str, Any]) -> str:
    """Build DDL for a single column."""
    name = col['name']
    col_type = normalize_type(col.get('type', 'STRING'))
    nullable = col.get('nullable', True)
    description = col.get('description', '')
    
    null_clause = "" if nullable else " NOT NULL"
    
    # Escape and truncate description
    desc = escape_sql_string(description)
    if len(desc) > 1000:
        desc = desc[:997] + "..."
    
    comment_clause = f"\n    COMMENT '{desc}'" if desc else ""
    
    return f"  {name} {col_type}{null_clause}{comment_clause}"


def build_create_table_ddl(
    catalog: str,
    schema: str,
    table_config: Dict[str, Any]
) -> str:
    """Build CREATE TABLE DDL from YAML configuration."""
    
    table_name = table_config['table_name']
    columns = table_config.get('columns', [])
    description = table_config.get('description', '')
    domain = table_config.get('domain', 'unknown')
    bronze_source = table_config.get('bronze_source', '')
    
    # Build columns
    column_ddls = [build_column_ddl(col) for col in columns]
    columns_str = ",\n".join(column_ddls)
    
    # Build properties
    props = STANDARD_PROPERTIES.copy()
    props['domain'] = domain
    props['entity_type'] = "dimension" if table_name.startswith("dim_") else "fact"
    if bronze_source:
        props['bronze_source'] = escape_sql_string(bronze_source)
    
    props_str = ",\n    ".join([f"'{k}' = '{v}'" for k, v in props.items()])
    
    # Build table comment
    table_comment = escape_sql_string(description.strip() if description else f"Gold {domain} table")
    
    return f"""CREATE OR REPLACE TABLE {catalog}.{schema}.{table_name} (
{columns_str}
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    {props_str}
)
COMMENT '{table_comment}'"""


def build_pk_ddl(
    catalog: str,
    schema: str,
    table_name: str,
    pk_config: Dict[str, Any]
) -> Optional[str]:
    """Build ALTER TABLE DDL for primary key constraint."""
    
    if not pk_config:
        return None
    
    pk_columns = pk_config.get('columns', [])
    if not pk_columns:
        return None
    
    pk_cols_str = ", ".join(pk_columns)
    
    return f"""ALTER TABLE {catalog}.{schema}.{table_name}
ADD CONSTRAINT pk_{table_name}
PRIMARY KEY ({pk_cols_str})
NOT ENFORCED"""


# ============================================================================
# TABLE CREATION
# ============================================================================

def create_table(
    spark: SparkSession,
    catalog: str,
    schema: str,
    yaml_path: Path
) -> Dict[str, Any]:
    """Create a single table from YAML file."""
    
    result = {
        "file": yaml_path.name,
        "table": None,
        "status": "unknown",
        "message": ""
    }
    
    try:
        # Load YAML
        config = load_yaml(yaml_path)
        table_name = config.get('table_name', yaml_path.stem)
        result["table"] = table_name
        
        # Create table
        create_ddl = build_create_table_ddl(catalog, schema, config)
        spark.sql(create_ddl)
        
        # Add primary key
        pk_config = config.get('primary_key', {})
        pk_ddl = build_pk_ddl(catalog, schema, table_name, pk_config)
        
        pk_status = ""
        if pk_ddl:
            try:
                spark.sql(pk_ddl)
                pk_cols = pk_config.get('columns', [])
                pk_status = f" (PK: {', '.join(pk_cols)})"
            except Exception as e:
                if "already exists" in str(e).lower():
                    pk_status = " (PK exists)"
                else:
                    pk_status = f" (PK failed)"
        
        result["status"] = "success"
        result["message"] = f"Created{pk_status}"
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)[:150]
    
    return result


def create_domain_tables(
    spark: SparkSession,
    catalog: str,
    schema: str,
    domain: str,
    yaml_base: Path
) -> List[Dict[str, Any]]:
    """Create all tables for a domain."""
    
    yaml_files = get_domain_yamls(yaml_base, domain)
    
    if not yaml_files:
        print(f"  ⚠ No YAML files found for domain: {domain}")
        return []
    
    results = []
    for yaml_file in yaml_files:
        result = create_table(spark, catalog, schema, yaml_file)
        results.append(result)
        
        icon = "✓" if result["status"] == "success" else "❌"
        print(f"   {icon} {result['table']}: {result['message']}")
    
    return results


# ============================================================================
# MAIN
# ============================================================================

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    domain = dbutils.widgets.get("domain")  # 'all' or specific domain name
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Domain: {domain}")
    print()
    
    return catalog, gold_schema, domain


def main():
    """Main entry point - creates Gold tables from YAML definitions."""
    
    catalog, gold_schema, domain = get_parameters()
    
    spark = SparkSession.builder.appName("Health Monitor Gold Setup").getOrCreate()
    
    print("=" * 80)
    print("HEALTH MONITOR - GOLD LAYER SETUP (YAML-DRIVEN)")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {gold_schema}")
    print(f"Domain: {domain}")
    print("=" * 80)
    print()
    
    try:
        # Find YAML base directory
        yaml_base = find_yaml_base()
        print(f"📁 YAML Base: {yaml_base}")
        print()
        
        # Determine which domains to process
        if domain.lower() == "all":
            domains = get_all_domains(yaml_base)
        else:
            domains = [domain]
        
        print(f"Processing {len(domains)} domain(s): {', '.join(domains)}")
        print()
        
        # Process each domain
        total_success = 0
        total_errors = 0
        
        for d in domains:
            print(f"📦 {d.upper()}")
            print("-" * 40)
            
            results = create_domain_tables(spark, catalog, gold_schema, d, yaml_base)
            
            for r in results:
                if r["status"] == "success":
                    total_success += 1
                else:
                    total_errors += 1
            
            print()
        
        # Summary
        print("=" * 80)
        print("✅ GOLD LAYER SETUP COMPLETE")
        print("=" * 80)
        print(f"Domains: {len(domains)}")
        print(f"Tables created: {total_success}")
        print(f"Errors: {total_errors}")
        print()
        
        if total_errors > 0:
            print("⚠️  Some tables had errors. Review output above.")
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ SETUP FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

