# pip install streamlit
# streamlit run chat.py

# import streamlit as st
# import pandas as pd
# import numpy as np

# st.title("Chat with IMDb data")

from openai import OpenAI
import json
from google.cloud import bigquery

client = OpenAI()

# TODO: add the schema of the IMDb database (BigQuery) in the prompt by reading it from BigQuery


def get_prompt(schema):
    base_prompt = """
You are an assistant that answer movies related questions.
"""
    for table in schema:
        base_prompt += f"\nTable: `{table['name']}`\n"
        for column in table["schema"]:
            base_prompt += f"- {column['name']} ({column['type']})\n"
            if column["type"] == "RECORD" and column["fields"]:
                for field in column["fields"]:
                    base_prompt += f"\t- {field['name']} ({field['type']})\n"
    return base_prompt


def column_to_dict(column):
    result = {"name": column.name, "type": column.field_type}
    if column.field_type == "RECORD" and column.fields:
        result["fields"] = [column_to_dict(field) for field in column.fields]
    return result


def get_schema():
    client = bigquery.Client(project="ensai-2026")
    dataset_id = "silver_christophe"
    tables = ["movies", "dim_actors", "dim_directors"]

    schema = []
    client.get_dataset(dataset_id)
    for table in tables:
        table_schema = client.get_table(f"{dataset_id}.{table}").schema
        table_schema = [column_to_dict(column) for column in table_schema]
        schema.append({"name": dataset_id + "." + table, "schema": table_schema})
    return schema


def execute_sql(sql_query):
    print("Executing SQL query...")
    client = bigquery.Client(project="ensai-2026")
    query_job = client.query(sql_query)
    results = query_job.result()
    return results.to_dataframe().to_string()


tools = [
    {
        "type": "function",
        "name": "execute_sql",
        "description": "Execute a SQL query on the IMDb database (BigQuery).",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "SQL query to execute on the IMDb database (BigQuery).",
                }
            },
            "required": ["sql_query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def run_agent(prompt):
    print("Running agent...")
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": input("What do you want to know about the IMDb database?"),
        },
    ]
    should_continue = True
    while should_continue:
        response = client.responses.create(
            model="gpt-5.2",
            input=messages,
            tools=tools,  # type: ignore
            reasoning=None,
        )

        for output in response.output:
            if output.type == "function_call":
                messages.append(output.model_dump())
                if output.name == "execute_sql":
                    result = execute_sql(json.loads(output.arguments)["sql_query"])
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": output.call_id,
                            "output": json.dumps({"result": result}),
                        }
                    )
            else:
                should_continue = False

        print(response.output_text)


schema = get_schema()
prompt = get_prompt(schema)
run_agent(prompt)
