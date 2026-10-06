from rich.console import Console

console = Console()


def display_findings(title, findings):
    """Display scanner findings in a readable format."""
    console.print(f"\n[bold blue]{title}[/bold blue]")

    if not findings:
        console.print("[green]No findings detected.[/green]")
        return

    for finding in findings:
        console.print(finding)


if __name__ == "__main__":
    console.print("[bold green]Cloud Infrastructure Auditor[/bold green]")
    console.print("Reporting module initialized successfully.")