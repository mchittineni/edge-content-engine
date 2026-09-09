"""
Pipeline Orchestrator: Coordinates the multi-agent editorial workflow
from Discovery & Scoring through to Research, Drafting, Code Validation,
and Human Approval Gate.
"""

from rich.console import Console

from apps.workers.dispatcher import AgentDispatcher
from packages.schemas import (
    AgentType,
    ArchitecturePackage,
    ArticleDraft,
    ArticleRecord,
    ArticleStatus,
    JobContract,
    OpportunityScore,
    QAReport,
    ResearchPackage,
    SEOBundle,
    SocialPackage,
)
from packages.storage import default_lake

console = Console()


class ArticlePipelineOrchestrator:
    def __init__(self):
        self.dispatcher = AgentDispatcher()

    async def run_pipeline(
        self,
        article_id: str,
        topic: str,
        category: str = "architecture",
        force_pass_score: bool = False,
    ) -> ArticleRecord:
        """
        Executes the end-to-end editorial pipeline up to the AWAITING_APPROVAL gate.
        """
        console.print(
            "\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]"
        )
        console.print(f"[bold white]LAUNCHING PIPELINE FOR: {article_id}[/bold white]")
        console.print(f"[dim cyan]Topic: {topic}[/dim cyan]")
        console.print(
            "[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]\n"
        )

        # Check existing state or initialize
        article = default_lake.load_article_state(article_id) or ArticleRecord(
            id=article_id, topic=topic, category=category, status=ArticleStatus.DISCOVERED
        )

        # Step 1: Scoring Agent
        console.print("[bold yellow]Step 1: Scoring Opportunity...[/bold yellow]")
        score_job = JobContract(
            article_id=article_id,
            agent=AgentType.SCORER,
            input_payload={"topic": topic, "category": category},
        )
        score_res = await self.dispatcher.dispatch(score_job)
        score = OpportunityScore.model_validate(score_res.output_payload["score"])
        article.score = score
        article.status = ArticleStatus.SCORED
        console.print(
            f"  → Score: [bold green]{score.total_score}/60[/bold green] (Decision: {score.recommendation})"
        )

        if score.total_score < 48 and not force_pass_score:
            console.print(
                "[yellow]Score below threshold (48). Moving to backlog. Stopping pipeline.[/yellow]"
            )
            default_lake.save_article_state(article)
            return article

        # Step 2: Research Agent
        console.print(
            "\n[bold yellow]Step 2: Conducting Rigorous Technical Research...[/bold yellow]"
        )
        article.status = ArticleStatus.RESEARCHING
        research_job = JobContract(
            article_id=article_id,
            agent=AgentType.RESEARCHER,
            input_payload={"topic": topic, "category": category},
        )
        research_res = await self.dispatcher.dispatch(research_job)
        research = ResearchPackage.model_validate(research_res.output_payload)
        article.research = research
        article.status = ArticleStatus.RESEARCHED
        default_lake.save_research(article_id, research.model_dump())
        console.print(
            f"  → Verified [bold green]{len(research.claims)}[/bold green] technical claims with primary sources."
        )

        # Step 3: Architecture Agent
        console.print(
            "\n[bold yellow]Step 3: Extracting Cloud Topology & Architecture Diagrams...[/bold yellow]"
        )
        arch_job = JobContract(
            article_id=article_id,
            agent=AgentType.ARCHITECT,
            input_payload={"topic": topic, "claims": [c.claim for c in research.claims]},
        )
        arch_res = await self.dispatcher.dispatch(arch_job)
        arch = ArchitecturePackage.model_validate(arch_res.output_payload)
        article.architecture = arch
        default_lake.save_diagram(article_id, "architecture.mmd", arch.mermaid_code)
        console.print("  → Generated Mermaid architecture topology and ASCII preview.")

        # Step 4: Writer Agent
        console.print(
            "\n[bold yellow]Step 4: Drafting 14-Section EDGE Technical Article...[/bold yellow]"
        )
        article.status = ArticleStatus.DRAFTING
        writer_job = JobContract(
            article_id=article_id,
            agent=AgentType.WRITER,
            input_payload={
                "topic": topic,
                "research": research.model_dump(),
                "architecture": arch.model_dump(),
            },
        )
        writer_res = await self.dispatcher.dispatch(writer_job)
        draft = ArticleDraft.model_validate(writer_res.output_payload)
        article.draft = draft
        article.status = ArticleStatus.DRAFTED
        default_lake.save_draft(article_id, draft.version, draft.full_markdown)
        console.print(
            f"  → Drafted article: [bold green]'{draft.title}'[/bold green] (v{draft.version})"
        )

        # Step 5: Code Validator Agent
        console.print("\n[bold yellow]Step 5: Running Code Sandboxing & Linters...[/bold yellow]")
        article.status = ArticleStatus.VALIDATING
        validator_job = JobContract(
            article_id=article_id,
            agent=AgentType.VALIDATOR,
            input_payload={"markdown": draft.full_markdown},
        )
        validator_res = await self.dispatcher.dispatch(validator_job)
        val_checks = validator_res.output_payload.get("checks", [])
        console.print(
            f"  → Validated [bold green]{len(val_checks)}[/bold green] embedded code blocks."
        )

        # Step 6: Fact-Checker & Technical QA
        console.print("\n[bold yellow]Step 6: Executing Technical QA & Fact-Check...[/bold yellow]")
        qa_job = JobContract(
            article_id=article_id,
            agent=AgentType.FACTCHECKER,
            input_payload={"draft": draft.model_dump(), "research": research.model_dump()},
        )
        qa_res = await self.dispatcher.dispatch(qa_job)
        qa = QAReport.model_validate(qa_res.output_payload)
        article.qa = qa
        console.print(
            f"  → Technical QA Score: [bold green]{qa.technical_score}/100[/bold green] | Citation Score: [bold green]{qa.citation_score}/100[/bold green]"
        )

        # Step 7: SEO Agent
        console.print(
            "\n[bold yellow]Step 7: Generating SEO Metadata & OpenGraph Tags...[/bold yellow]"
        )
        seo_job = JobContract(
            article_id=article_id,
            agent=AgentType.SEO,
            input_payload={"draft": draft.model_dump()},
        )
        seo_res = await self.dispatcher.dispatch(seo_job)
        seo = SEOBundle.model_validate(seo_res.output_payload)
        article.seo = seo
        article.status = ArticleStatus.AWAITING_APPROVAL
        console.print(
            f"  → Primary Keyword: [cyan]{seo.primary_keyword}[/cyan] | Slug: [cyan]{seo.slug}[/cyan]"
        )

        # Step 8: Social Repurposing (LinkedIn, Reddit, X)
        console.print(
            "\n[bold yellow]Step 8: Generating Platform-Specific Social Distribution...[/bold yellow]"
        )
        social_job = JobContract(
            article_id=article_id,
            agent=AgentType.SOCIAL,
            input_payload={"draft": draft.model_dump()},
        )
        social_res = await self.dispatcher.dispatch(social_job)
        social = SocialPackage.model_validate(social_res.output_payload)
        article.social = social
        console.print("  → Generated LinkedIn post, authentic Reddit discussion, and X thread.")

        # Persist complete state
        default_lake.save_article_state(article)

        console.print("\n[bold green]✓ Pipeline completed successfully![/bold green]")
        console.print(
            f"[bold white]Status: [cyan]AWAITING_APPROVAL[/cyan] — Ready for review via `edge review {article_id}`[/bold white]\n"
        )

        return article
