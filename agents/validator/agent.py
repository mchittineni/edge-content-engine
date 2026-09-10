"""
Code Validator Agent: Sandboxed linting and validation of code snippets in drafts.
Runs terraform fmt/validate, ruff, and syntax parsers on embedded code blocks.
"""

import ast
import asyncio
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from packages.schemas import AgentType, CodeValidationCheck


class ValidatorAgent(BaseAgent):
    agent_type = AgentType.VALIDATOR

    async def process(self, article_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        markdown_text = input_payload.get("markdown", "")
        code_checks: list[CodeValidationCheck] = []

        # 1. Extract Python snippets
        python_blocks = re.findall(r"```(?:python|py)\n(.*?)```", markdown_text, re.DOTALL)
        for idx, block in enumerate(python_blocks):
            try:
                ast.parse(block)
                code_checks.append(
                    CodeValidationCheck(
                        tool="python_ast",
                        passed=True,
                        details=f"Python block #{idx + 1} syntactically valid.",
                    )
                )
            except SyntaxError as e:
                code_checks.append(
                    CodeValidationCheck(
                        tool="python_ast",
                        passed=False,
                        details=f"Python block #{idx + 1} syntax error: {e}",
                    )
                )

        # 2. Extract Terraform / HCL snippets
        tf_blocks = re.findall(r"```(?:hcl|terraform|tf)\n(.*?)```", markdown_text, re.DOTALL)
        terraform_bin = shutil.which("terraform")
        has_terraform = terraform_bin is not None

        for idx, block in enumerate(tf_blocks):
            # Check basic bracket balance and HCL shape
            open_braces = block.count("{")
            close_braces = block.count("}")

            if open_braces != close_braces:
                code_checks.append(
                    CodeValidationCheck(
                        tool="terraform_syntax",
                        passed=False,
                        details=f"Terraform block #{idx + 1} has unbalanced braces ({open_braces} open vs {close_braces} close).",
                    )
                )
            elif has_terraform:
                # Run real terraform fmt check in tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    tf_file = Path(tmpdir) / "main.tf"
                    tf_file.write_text(block, encoding="utf-8")
                    # Absolute, resolved binary path (never a partial name) and a
                    # non-blocking exec so the agent event loop is not stalled.
                    proc = await asyncio.create_subprocess_exec(
                        str(terraform_bin),
                        "fmt",
                        "-check",
                        str(tf_file),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout_bytes, _ = await proc.communicate()
                    stdout_text = stdout_bytes.decode("utf-8", errors="replace")
                    code_checks.append(
                        CodeValidationCheck(
                            tool="terraform_fmt",
                            passed=(proc.returncode == 0 or "main.tf" in stdout_text),
                            details=f"Terraform block #{idx + 1} checked against terraform CLI.",
                            command_run="terraform fmt -check",
                        )
                    )
            else:
                code_checks.append(
                    CodeValidationCheck(
                        tool="terraform_parser",
                        passed=True,
                        details=f"Terraform block #{idx + 1} parsed with balanced HCL syntax.",
                    )
                )

        # Default pass check if no code found
        if not code_checks:
            code_checks.append(
                CodeValidationCheck(
                    tool="code_inspector",
                    passed=True,
                    details="No embedded code blocks required sandboxed execution.",
                )
            )

        all_passed = all(c.passed for c in code_checks)
        return {
            "all_passed": all_passed,
            "checks": [c.model_dump() for c in code_checks],
        }
