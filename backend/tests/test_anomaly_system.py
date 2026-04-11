import pytest
import json
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage

from backend.agents.anomaly_reasoner_agent import anomaly_reasoner_agent, AnomalyReasonerOutput, AnomalyHypothesis
from backend.agents.anomaly_checker_agent import anomaly_checker_agent

# ── Mock Data ────────────────────────────────────────────────────────────────

MOCK_RELEVANT_TABLES = ["mock_transactions"]
MOCK_SQL_RESULTS = [
    {"id": 1, "region": "SOUTH", "amount": 1000, "status": "FAILED"},
    {"id": 2, "region": "SOUTH", "amount": 2000, "status": "FAILED"},
]

# ── Tests ────────────────────────────────────────────────────────────────────

def test_anomaly_reasoner_success():
    """Verify that the reasoner produces hypotheses from LLM output."""
    
    # Mock LLM response
    mock_response = {
        "hypotheses": [
            {
                "title": "High Failures in SOUTH",
                "description": "The failure rate in SOUTH is unusual.",
                "verification_sql": "SELECT 0.75 AS metric_value",
                "condition": "metric_value > 0.5",
                "severity": "HIGH",
                "metric_label": "failure rate"
            }
        ],
        "reasoning": "Observed multiple failures in sample."
    }
    
    # Use RunnableLambda to satisfy LangChain's type checking for the | operator
    mock_runnable = RunnableLambda(lambda x: mock_response)

    with patch('backend.agents.anomaly_reasoner_agent.get_llm', return_value=mock_runnable), \
         patch('backend.agents.anomaly_reasoner_agent._fetch_table_schemas', return_value="Table: mock_transactions"):
        
        output = anomaly_reasoner_agent(
            user_query="Any anomalies?",
            relevant_tables=MOCK_RELEVANT_TABLES,
            sql_results=MOCK_SQL_RESULTS,
            team_id=str(uuid.uuid4()),
            current_date=date.today().isoformat()
        )
        
        assert output is not None
        assert len(output.hypotheses) == 1
        assert output.hypotheses[0].title == "High Failures in SOUTH"
        assert output.hypotheses[0].severity == "HIGH"


def test_anomaly_checker_success():
    """Verify that the checker confirms an anomaly when the SQL returns a triggering value."""
    
    hypothesis = AnomalyHypothesis(
        title="Spike detected",
        description="Spike in volume",
        verification_sql="SELECT 100 AS metric_value",
        condition="metric_value > 50",
        severity="MEDIUM",
        metric_label="volume"
    )
    reasoner_output = AnomalyReasonerOutput(hypotheses=[hypothesis], reasoning="test")
    
    # Mock session
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result._mapping = {"metric_value": 100.0}
    mock_session.execute.return_value.fetchone.return_value = mock_result
    
    with patch('backend.agents.anomaly_checker_agent.get_sync_session') as mock_get_session:
        # get_sync_session is a context manager
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        alerts = anomaly_checker_agent(reasoner_output, str(uuid.uuid4()))
        
        assert len(alerts) == 1
        assert alerts[0]["title"] == "Spike detected"
        assert alerts[0]["data_snapshot"]["metric_value"] == 100.0


def test_anomaly_checker_retry_logic():
    """Verify that the checker attempts to fix SQL on failure and succeeds on retry."""
    
    hypothesis = AnomalyHypothesis(
        title="Flaky SQL",
        description="SQL might fail once",
        verification_sql="SELECT 1 AS metric_value FROM non_existent_table",
        condition="metric_value > 0",
        severity="LOW",
        metric_label="test"
    )
    reasoner_output = AnomalyReasonerOutput(hypotheses=[hypothesis], reasoning="test")
    
    # Mock session: fail first, succeed second
    mock_session = MagicMock()
    mock_res_ok = MagicMock()
    mock_res_ok._mapping = {"metric_value": 5.0}
    
    mock_session.execute.side_effect = [
        Exception("Table 'non_existent_table' not found"),
        MagicMock(fetchone=lambda: mock_res_ok)
    ]
    
    # Mock SQL Fixer
    mock_fix_output = {"fixed_sql": "SELECT 5 AS metric_value"}
    mock_runnable = RunnableLambda(lambda x: mock_fix_output)
    
    with patch('backend.agents.anomaly_checker_agent.get_sync_session') as mock_get_session, \
         patch('backend.agents.anomaly_checker_agent.get_llm', return_value=mock_runnable):
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        alerts = anomaly_checker_agent(reasoner_output, str(uuid.uuid4()))
        
        assert len(alerts) == 1
        assert alerts[0]["data_snapshot"]["metric_value"] == 5.0
        assert mock_session.execute.call_count == 2 # Initial + Retry


def test_anomaly_checker_safety():
    """Verify that the checker blocks unsafe/malicious SQL."""
    
    hypothesis = AnomalyHypothesis(
        title="Exploit",
        description="Try to drop tables",
        verification_sql="DROP TABLE users; SELECT 1 AS metric_value",
        condition="metric_value > 0",
        severity="HIGH",
        metric_label="malicious"
    )
    reasoner_output = AnomalyReasonerOutput(hypotheses=[hypothesis], reasoning="test")
    
    alerts = anomaly_checker_agent(reasoner_output, str(uuid.uuid4()))
    
    # Safety check should catch "DROP" and return no alerts
    assert len(alerts) == 0
