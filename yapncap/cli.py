import typer
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from yapncap.config import YapnCapConfig, load_config, save_config, validate_config
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
        
    console.print(f"Fact-checking [bold cyan]{url}[/bold cyan] using {config.provider.capitalize()} ({config.intensity} mode)...")
    # TODO: Implement fact-checking pipeline

if __name__ == "__main__":
    app()
