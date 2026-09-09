import pytest
from agents.validator.agent import ValidatorAgent
from packages.schemas import JobContract, AgentType


@pytest.mark.asyncio
async def test_validator_detects_syntax_errors():
    validator = ValidatorAgent()

    # Broken Python
    broken_markdown = (
        "Here is some broken Python:\n\n"
        "```python\ndef bad_syntax(\n    return 42\n```\n"
    )

    job = JobContract(
        article_id="TEST-001",
        agent=AgentType.VALIDATOR,
        input_payload={"markdown": broken_markdown},
    )

    res = await validator.execute_job(job)
    checks = res.output_payload.get("checks", [])
    python_check = next((c for c in checks if c["tool"] == "python_ast"), None)
    assert python_check is not None
    assert python_check["passed"] is False


@pytest.mark.asyncio
async def test_validator_passes_valid_code():
    validator = ValidatorAgent()

    valid_markdown = (
        "Here is valid code:\n\n"
        "```python\ndef get_cluster_name() -> str:\n    return 'edge-prod-cluster'\n```\n"
    )

    job = JobContract(
        article_id="TEST-002",
        agent=AgentType.VALIDATOR,
        input_payload={"markdown": valid_markdown},
    )

    res = await validator.execute_job(job)
    checks = res.output_payload.get("checks", [])
    assert any(c["tool"] == "python_ast" and c["passed"] is True for c in checks)
