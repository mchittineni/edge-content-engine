"""
Discovery Bot: Watches GitHub repositories, releases, benchmarks, and cloud ecosystems.
"""

from typing import Any

from agents.base import BaseAgent
from packages.schemas import AgentType


class DiscoveryAgent(BaseAgent):
    agent_type = AgentType.DISCOVERY

    async def process(self, article_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        repo_name = input_payload.get("repo_name", "mchittineni/tf-arch-diagram-generator")

        # Discover potential story ideas
        opportunities: list[dict[str, Any]] = [
            {
                "topic": "Terraform plans are terrible architecture diagrams",
                "category": "architecture",
                "source": f"GitHub: {repo_name}",
                "context": "Developers spend hours reviewing 1,500-line plan outputs without spatial topology.",
            },
            {
                "topic": "I Added 23 Terraform Security Tests — Here Is What Broke",
                "category": "security",
                "source": "IaCSecBench / Policy Benchmarks",
                "context": "Benchmarking OPA / Checkov rules against real-world production Terraform modules.",
            },
            {
                "topic": "Why AWS OIDC Authentication Makes Long-Lived CI Secrets Obsolete",
                "category": "devsecops",
                "source": "GitHub Actions + AWS IAM",
                "context": "Short-lived JWT exchange eliminates static IAM secret leaks in CI/CD pipelines.",
            },
        ]

        return {
            "discovered_count": len(opportunities),
            "opportunities": opportunities,
        }
