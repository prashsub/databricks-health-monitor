# Databricks notebook source
"""
Validate SQL benchmark questions for a single Genie Space.
Parameters:
  - catalog: Catalog name
  - gold_schema: Gold schema name
  - feature_schema: Feature schema name (for ML tables)
  - genie_space: Name of the Genie Space to validate (e.g., 'cost_intelligence_genie')
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import json
from pathlib import Path

# COMMAND ----------

def get_parameters():
    """Get notebook parameters."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    genie_space = dbutils.widgets.get("genie_space")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    print(f"Genie Space: {genie_space}")
    
    return catalog, gold_schema, feature_schema, genie_space

# COMMAND ----------

def substitute_variables(sql, catalog, gold_schema, feature_schema):
    """Substitute variables in SQL."""
    sql = sql.replace("${catalog}", catalog)
    sql = sql.replace("${gold_schema}", gold_schema)
    sql = sql.replace("${feature_schema}", feature_schema)
    return sql

# COMMAND ----------

def validate_sql(spark, sql, question_id):
    """Validate SQL using EXPLAIN."""
    try:
        spark.sql(f"EXPLAIN {sql}")
        return True, None
    except Exception as e:
        error_msg = str(e)
        
        # Categorize error
        if "UNRESOLVED_COLUMN" in error_msg or "COLUMN_NOT_FOUND" in error_msg:
            error_type = "COLUMN_NOT_FOUND"
        elif "TABLE_OR_VIEW_NOT_FOUND" in error_msg or "TABLE_NOT_FOUND" in error_msg:
            error_type = "TABLE_NOT_FOUND"
        elif "UNRESOLVABLE_TABLE_VALUED_FUNCTION" in error_msg:
            error_type = "TVF_NOT_FOUND"
        elif "WRONG_NUM_ARGS" in error_msg:
            error_type = "WRONG_NUM_ARGS"
        else:
            error_type = "OTHER"
        
        # Extract first line of error
        error_summary = error_msg.split('\n')[0][:200]
        
        return False, {
            'question_id': question_id,
            'error_type': error_type,
            'error_message': error_summary
        }

# COMMAND ----------

def validate_genie_space(spark, catalog, gold_schema, feature_schema, genie_space):
    """Validate all benchmark questions for a Genie Space."""
    
    # Load JSON export
    json_path = f"/Workspace/Users/prashanth.subrahmanyam@databricks.com/.bundle/databricks_health_monitor/dev/files/src/genie/{genie_space}_export.json"
    
    try:
        with open(json_path, 'r') as f:
            export_data = json.load(f)
    except FileNotFoundError:
        raise Exception(f"JSON file not found: {json_path}")
    
    if 'benchmarks' not in export_data or 'questions' not in export_data['benchmarks']:
        raise Exception(f"No benchmark questions found in {json_path}")
    
    questions = export_data['benchmarks']['questions']
    print(f"\n{'='*80}")
    print(f"Validating: {genie_space} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    for idx, q in enumerate(questions, 1):
        question_text = q.get('question', ['Unknown'])[0] if isinstance(q.get('question'), list) else 'Unknown'
        
        if 'answer' not in q:
            print(f"⚠️  Q{idx}: Missing answer field")
            invalid_count += 1
            continue
        
        answers = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
        
        if not answers:
            print(f"⚠️  Q{idx}: Empty answer")
            invalid_count += 1
            continue
        
        answer = answers[0]
        if answer.get('format') != 'SQL':
            print(f"⚠️  Q{idx}: Not SQL format")
            invalid_count += 1
            continue
        
        content = answer.get('content', [])
        if isinstance(content, list):
            sql = '\n'.join(content)
        else:
            sql = content
        
        # Substitute variables
        sql = substitute_variables(sql, catalog, gold_schema, feature_schema)
        
        # Validate
        is_valid, error = validate_sql(spark, sql, f"Q{idx}")
        
        if is_valid:
            print(f"✅ Q{idx}: {question_text[:60]}...")
            valid_count += 1
        else:
            print(f"❌ Q{idx}: {error['error_type']} - {question_text[:60]}...")
            print(f"   Error: {error['error_message']}")
            invalid_count += 1
            errors.append(error)
    
    print(f"\n{'='*80}")
    print(f"Validation Summary for {genie_space}")
    print(f"{'='*80}")
    print(f"✅ Valid: {valid_count}/{len(questions)}")
    print(f"❌ Invalid: {invalid_count}/{len(questions)}")
    
    if errors:
        print(f"\nError Breakdown:")
        error_types = {}
        for err in errors:
            error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count}")
    
    return valid_count, invalid_count, errors

# COMMAND ----------

def main():
    """Main entry point."""
    catalog, gold_schema, feature_schema, genie_space = get_parameters()
    
    spark = SparkSession.builder.appName(f"Validate {genie_space}").getOrCreate()
    
    try:
        valid_count, invalid_count, errors = validate_genie_space(
            spark, catalog, gold_schema, feature_schema, genie_space
        )
        
        if invalid_count > 0:
            raise Exception(
                f"Validation failed: {invalid_count} queries with errors in {genie_space}\n\n"
                f"First 5 errors:\n" + 
                '\n'.join([f"  - {e['question_id']}: {e['error_type']} - {e['error_message']}" 
                          for e in errors[:5]])
            )
        
        print(f"\n✅ SUCCESS: All {valid_count} queries validated for {genie_space}!")
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()



