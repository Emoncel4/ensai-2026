# pip install streamlit
# streamlit run chat.py

# import streamlit as st
# import pandas as pd
# import numpy as np

# st.title("Chat with IMDb data")

from openai import OpenAI
import json

client = OpenAI()

prompt = """
You are an assistant that answer movies related questions.
"""
# TODO: add the schema of the IMDb database (BigQuery) in the prompt by reading it from BigQuery


def execute_sql(sql_query):
    # TODO: write function to execute sql query on BigQuery
    return []


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

response = client.responses.create(
    model="gpt-5-nano",
    input=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": "What is the last movie of Brad Pitt?"},
    ],
    tools=tools,  # type: ignore
    reasoning=None,
)

for output in response.output:
    if output.type == "function_call":
        if output.name == "execute_sql":
            result = execute_sql(json.loads(output.arguments)["sql_query"])
            print(result)
