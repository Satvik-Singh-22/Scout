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
If normal databases store clear rows and columns of facts, our "Chroma manager" stores feelings and thoughts!
It runs our special Vector Database (ChromaDB), which holds text documents (like customer reviews) 
in a way that lets the AI search them by "meaning" rather than just exact keywords. 
This file gets that special database ready so our RAG agent can quickly fetch relevant paragraphs.
"""
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

_vectorstore = None
_slack_vectorstore = None
_jira_vectorstore = None

def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        _vectorstore = Chroma(
            collection_name="customer_reviews",
            embedding_function=embeddings,
            persist_directory=os.getenv(
                "CHROMA_PERSIST_PATH",
                "./chroma_data"
            )
        )
    return _vectorstore


def get_slack_vectorstore() -> Chroma:
    global _slack_vectorstore
    if _slack_vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _slack_vectorstore = Chroma(
            collection_name="slack_messages",
            embedding_function=embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")
        )
    return _slack_vectorstore


def get_jira_vectorstore() -> Chroma:
    global _jira_vectorstore
    if _jira_vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _jira_vectorstore = Chroma(
            collection_name="jira_tickets",
            embedding_function=embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")
        )
    return _jira_vectorstore


def get_retriever():
    return get_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5}
    )


def get_slack_retriever(k=15):
    return get_slack_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def get_jira_retriever(k=15):
    return get_jira_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )