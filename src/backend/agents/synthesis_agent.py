# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ELI5 (What does this file do?):
Think of this file as the ultimate compiler or meeting note-taker. 
Usually, we have raw numbers from the database (like "Revenue: $5,000") and clunky text pieces from documents.
This file takes all those puzzle pieces and mashes them together into a single, cohesive, factual draft. 
It says, "Based on the numbers and the text we found, here is the complete factual picture." 
It doesn't worry about being polite or sounding like an executive—it just gets the absolute facts straight.
"""
from langchain_core.prompts import ChatPromptTemplate
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState
import json

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data synthesis agent. 
Combine the structured query results and unstructured text excerpts into a coherent factual summary. Do not leave out any important information.
Do not format for a user yet — this summary will be further processed.
Be complete and accurate. Include all numbers and key findings.
"""),
    ("human", """Original question: {user_query}

SQL query results (structured data):
{sql_results}

Relevant text excerpts (unstructured data):
{rag_chunks}

Provide a complete factual synthesis:""")
])

def format_sql_results(results: list) -> str:
    if not results:
        return "No SQL data available."
    return json.dumps(results[:20], indent=2, default=str)

def format_rag_chunks(chunks: list) -> str:
    if not chunks:
        return "No text data available."
    formatted = ""
    for i, chunk in enumerate(chunks):
        formatted += f"{i+1}. {chunk}\n"
    return formatted

def synthesis_agent(state: PipelineState) -> dict:
    # If there is no data to synthesize, return an empty context
    if not state.get("sql_results") and not state.get("rag_chunks"):
        return {"synthesized_context": "No relevant data found for the query."}

    sql_str = format_sql_results(state.get("sql_results", []))
    rag_str = format_rag_chunks(state.get("rag_chunks", []))
    
    llm = get_llm(temperature=0)
    chain = SYNTHESIS_PROMPT | llm
    
    result = chain.invoke({
        "user_query": state["user_query"],
        "sql_results": sql_str,
        "rag_chunks": rag_str
    })
    print("[DEBUG] SYNTHESIS AGENT")
    return {"synthesized_context": result.content}
