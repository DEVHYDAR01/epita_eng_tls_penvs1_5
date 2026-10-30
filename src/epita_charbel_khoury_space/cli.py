from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from epita_charbel_khoury_space.client import fetch_live_data

console = Console()

def main():
    try:
        data = fetch_live_data()
        table = Table(title=f"Live System Telemetry: {data.get('status')}")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        for key, value in data.items():
            table.add_row(str(key), str(value))

        console.print(Panel(table, title="EPITA Engineering Tools — Session 2", expand=False))
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
