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
        
    console.print(f"Extracting transcript from [bold cyan]{url}[/bold cyan]...")
    try:
        result = get_transcript(url, config.language)
        
        # --- Phase 5: Header Panel ---
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
        
        no_cap_count = 0
        cap_count = 0
        yappin_count = 0
        
        for c in claims:
            if c.verdict == "NO CAP":
                verdict_badge = "[bold green]🟢 NO CAP[/bold green]"
                no_cap_count += 1
            elif c.verdict == "CAP":
                verdict_badge = "[bold red]🔴 CAP![/bold red]"
                cap_count += 1
            else:
                verdict_badge = "[bold yellow]🟡 YAPPIN[/bold yellow]"
                yappin_count += 1
                
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
            f"🟢 NO CAP: {no_cap_count} ({int((no_cap_count/total)*100)}%)\n"
            f"🔴 CAP!:   {cap_count} ({int((cap_count/total)*100)}%)\n"
            f"🟡 YAPPIN: {yappin_count} ({int((yappin_count/total)*100)}%)"
        )
        console.print(Panel(summary_text, title="[bold magenta]Summary[/bold magenta]", border_style="magenta", expand=False))
        
    except Exception as e:
        console.print(f"[bold red]Error extracting video:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    app()
