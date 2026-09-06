import typer
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich.text import Text
from rich import box
from yapncap.config import YapnCapConfig, load_config, save_config, validate_config
from yapncap.extractor import get_transcript
from yapncap.engine import fact_check
import sys
import json
import re
from datetime import datetime

app = typer.Typer(help="YapnCap 🧢 — Detect if they are just yappin' and cappin' in real-time.")
console = Console()

@app.command()
def setup():
    """
    Interactive first-time configuration wizard.
    """
    console.print("[bold green]Welcome to YapnCap 🧢 Setup![/bold green]")
    
    language = Prompt.ask("Select language", choices=["en", "id"], default="en")
    
    console.print("\n[bold]Select AI Provider:[/bold]")
    console.print("1. Gemini (Recommended - Supports Search Grounding)")
    console.print("2. OpenAI")
    console.print("3. Groq")
    provider_choice = IntPrompt.ask("Enter number", choices=["1", "2", "3"], default=1)
    provider_map = {1: "gemini", 2: "openai", 3: "groq"}
    provider = provider_map[provider_choice]
    
    api_key = Prompt.ask(f"Enter your {provider.capitalize()} API Key", password=True)
    
    console.print("\n[bold]Fact-Check Intensity:[/bold]")
    console.print("1. Lenient (Major claims only)")
    console.print("2. Balanced (Numbers, policies, significant statements)")
    console.print("3. Strict (Every verifiable detail)")
    intensity_choice = IntPrompt.ask("Enter number", choices=["1", "2", "3"], default=2)
    intensity_map = {1: "lenient", 2: "balanced", 3: "strict"}
    intensity = intensity_map[intensity_choice]
    
    config = YapnCapConfig(
        language=language,
        provider=provider,
        api_key=api_key,
        intensity=intensity
    )
    save_config(config)
    console.print("\n[bold green]✅ Configuration saved successfully![/bold green] You're ready to yap.")

@app.command()
def check(
    url: str = typer.Argument(..., help="YouTube URL to fact-check"),
    provider: str = typer.Option(None, "--provider", "-p", help="Override AI provider (gemini/openai/groq)"),
    intensity: str = typer.Option(None, "--intensity", "-i", help="Override fact-check intensity (lenient/balanced/strict)"),
    export_format: str = typer.Option(None, "--export", "-e", help="Export format (md/json)")
):
    """
    Fact-check a YouTube video URL.
    """
    config = load_config()
    
    # Apply CLI overrides
    if provider: config.provider = provider
    if intensity: config.intensity = intensity
    
    if not validate_config(config):
        console.print("[bold red]Error: Missing API key.[/bold red]")
        console.print("Please run [bold cyan]yapncap setup[/bold cyan] first, or set the appropriate environment variable (e.g. GEMINI_API_KEY).")
        sys.exit(1)
    try:
        # --- Phase 5: Header Panel (Wait, metadata needs to be fetched first, but get_transcript does both) ---
        # Actually, since get_transcript does both and could take a while for STT, we'll wrap it in a spinner.
        with Status(f"[bold cyan]Extracting CC or transcribing audio from {url}...[/bold cyan]", spinner="dots"):
            result = get_transcript(url, config)
            
        metadata_text = (
            f"[bold]Title:[/bold]    {result.title}\n"
            f"[bold]Channel:[/bold]  {result.channel}\n"
            f"[bold]Duration:[/bold] {result.duration}\n"
            f"[bold]Source:[/bold]   {result.source.upper()}"
        )
        console.print(Panel(metadata_text, title="[bold blue]Video Info[/bold blue]", border_style="blue", expand=False))
        
        # --- Phase 5: Processing Animation ---
        with Status(f"[bold yellow]Fact-checking with {config.provider.capitalize()} ({config.intensity})...[/bold yellow]", spinner="dots"):
            claims = fact_check(result.text, config)
        
        if not claims:
            console.print("\n[yellow]No factual claims found to check.[/yellow]")
            return
            
        # --- Phase 5: Results Table ---
        table = Table(box=box.ROUNDED, expand=True, show_lines=True)
        table.add_column("Verdict", justify="center", style="bold", width=10)
        table.add_column("Time", justify="center", style="cyan", width=13)
        table.add_column("Claim & Fact-Check", justify="left")
        
        fact_count = 0
        hoax_count = 0
        yapping_count = 0
        
        for c in claims:
            verdict_norm = c.verdict.upper().strip()
            if verdict_norm in ["FACT", "NO CAP"]:
                verdict_badge = "[bold green]🟢 FACT[/bold green]"
                fact_count += 1
            elif verdict_norm in ["HOAX", "CAP", "CAP!"]:
                verdict_badge = "[bold red]🔴 HOAX[/bold red]"
                hoax_count += 1
            else:
                verdict_badge = "[bold yellow]🟡 YAPPING[/bold yellow]"
                yapping_count += 1
                
            claim_text = (
                f"[bold white]{c.claim}[/bold white]\n"
                f"[dim]→ {c.correction}[/dim]\n"
                f"[blue][link={c.source}]Source[/link][/blue]: {c.source}"
            )
            
            table.add_row(verdict_badge, f"{c.time_start} - {c.time_end}", claim_text)
            
        console.print("\n")
        console.print(table)
        
        # --- Phase 5: Summary Footer ---
        total = len(claims)
        summary_text = (
            f"Total Claims Analyzed: [bold]{total}[/bold]\n"
            f"🟢 FACT:    {fact_count} ({int((fact_count/total)*100)}%)\n"
            f"🔴 HOAX:    {hoax_count} ({int((hoax_count/total)*100)}%)\n"
            f"🟡 YAPPING: {yapping_count} ({int((yapping_count/total)*100)}%)"
        )
        console.print(Panel(summary_text, title="[bold magenta]Summary[/bold magenta]", border_style="magenta", expand=False))
        
        # --- Phase 6: Export ---
        if export_format:
            # Generate safe filename
            safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', result.title.replace(' ', '_'))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = export_format.lower()
            filename = f"yapncap_{safe_title}_{timestamp}.{ext}"
            
            if ext == "json":
                export_data = {
                    "video": {
                        "title": result.title,
                        "channel": result.channel,
                        "url": result.url,
                        "duration": result.duration,
                        "source": result.source,
                    },
                    "summary": {
                        "total": total,
                        "fact": fact_count,
                        "hoax": hoax_count,
                        "yapping": yapping_count
                    },
                    "claims": [__import__("dataclasses").asdict(c) for c in claims]
                }
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                console.print(f"\n[bold green]✓ Exported JSON to:[/bold green] {filename}")
                
            elif ext == "md":
                md_lines = [
                    f"# YapnCap Report: {result.title}",
                    "",
                    f"**Channel:** {result.channel}  ",
                    f"**URL:** {result.url}  ",
                    f"**Duration:** {result.duration}  ",
                    f"**Transcript Source:** {result.source.upper()}  ",
                    "",
                    "## Summary",
                    f"- Total Claims: **{total}**",
                    f"- 🟢 **FACT:** {fact_count}",
                    f"- 🔴 **HOAX:** {hoax_count}",
                    f"- 🟡 **YAPPING:** {yapping_count}",
                    "",
                    "## Detailed Claims",
                    ""
                ]
                
                for c in claims:
                    md_lines.append(f"### [{c.verdict.upper()}] {c.time_start} - {c.time_end}")
                    md_lines.append(f"**Claim:** {c.claim}")
                    md_lines.append(f"**Explanation:** {c.correction}")
                    md_lines.append(f"**Source:** [Link]({c.source})")
                    md_lines.append("")
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(md_lines))
                console.print(f"\n[bold green]✓ Exported Markdown to:[/bold green] {filename}")
            else:
                console.print(f"\n[bold red]Unsupported export format: {ext}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error extracting video:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    app()
