"""Demo script for showcasing the agentic workflow.

When executed this script will:
1. Build a computational graph of the target spreadsheet.
2. Dispatch ExcelVariableAgent to extract variable names/descriptions/code with an LLM.
3. Display a concise log of extracted variables.
4. Dispatch ProgrammerAgent to organise everything into well-documented python code inside the same project directory.

Run the script in a terminal side-by-side with your file explorer for a compelling recording.
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from llm_agents.cell_inspectors import ExcelVariableAgent
from llm_agents.programmer import ProgrammerAgent

# ----------------------------------------------------------------------------
# Utility helpers
# ----------------------------------------------------------------------------


def banner(title: str, char: str = "=") -> None:
    """Pretty print a section banner."""
    border = char * len(title)
    print(f"\n{border}\n{title}\n{border}\n", flush=True)


def bullet(message: str) -> None:
    """Print a single level bullet point."""
    print(f"  • {message}", flush=True)


# ----------------------------------------------------------------------------
# Main demo logic
# ----------------------------------------------------------------------------


async def main(spreadsheet_path: Path) -> None:
    start_ts = datetime.now()

    # Extract names / paths --------------------------------------------------
    spreadsheet_path = spreadsheet_path.expanduser().resolve()
    spreadsheet_name = spreadsheet_path.stem
    path = spreadsheet_path.as_posix()

    # STEP 1 -----------------------------------------------------------------
    banner("STEP 1 / 6  –  Initialising ExcelVariableAgent")
    variable_agent = ExcelVariableAgent(
        spread_sheet_path=path,
        openai_model="gpt-4.1-mini",
        trace_with_langfuse=True,
    )
    bullet("ExcelVariableAgent ready ✓")

    # STEP 2 -----------------------------------------------------------------
    banner("STEP 2 / 6  –  Building & Visualising Computational Graph")
    graph_save_path = (
        Path(variable_agent.project_dir) / f"computegraph_{spreadsheet_name}.png"
    ).as_posix()
    variable_agent.graph.visualize(
        figsize=(8, 12),
        node_size=1200,
        title=spreadsheet_name,
        save_path=graph_save_path,
    )
    bullet(f"Graph saved to {graph_save_path}")

    # STEP 3 -----------------------------------------------------------------
    banner("STEP 3 / 6  –  Extracting Variables via LLM")
    await variable_agent.orchestrate_variable_extraction()
    bullet(
        f"Variable extraction finished – captured {len(variable_agent.variable_db)} cells"
    )

    # Display a concise preview of extracted variables (first 15 only)
    preview_limit = 15
    print("\nExtracted variables (preview):", flush=True)
    for i, ((sheet, cell), meta) in enumerate(variable_agent.variable_db.items()):
        if i >= preview_limit:
            bullet("… (truncated) …")
            break
        var_name = meta.get("variable_name")
        var_desc = meta.get("variable_desr")
        print(f"  {sheet}!{cell:<6} → {var_name}  # {var_desc}", flush=True)

    # STEP 4 -----------------------------------------------------------------
    banner("STEP 4 / 6  –  Persisting Variable Database")
    db_file = (
        Path(variable_agent.project_dir) / f"variable_db_{spreadsheet_name}.pkl"
    ).as_posix()
    bullet(f"Variable database saved to {db_file}")

    # STEP 5 -----------------------------------------------------------------
    banner("STEP 5 / 6  –  Initialising ProgrammerAgent")
    programmer = ProgrammerAgent(
        spread_sheet_path=path,
        openai_model="gpt-4.1",
        trace_with_langfuse=True,
    )
    bullet("ProgrammerAgent ready ✓")

    # STEP 6 -----------------------------------------------------------------
    banner("STEP 6 / 6  –  Generating Well-documented Python Code")
    await programmer.initialize_coding_agent()
    bullet("Code generation finished. Check the simple_beam directory for new files.")

    # SUMMARY ---------------------------------------------------------------
    elapsed = datetime.now() - start_ts
    banner("DEMO COMPLETE")
    print(f"Total elapsed time: {elapsed}\n", flush=True)


def _parse_args() -> Path:
    """Parse command-line arguments and return a Path to the spreadsheet."""
    default_path = Path("examples/simple_beam/simple_beam.xlsx")
    parser = argparse.ArgumentParser(
        description="Run the agentic spreadsheet → python demo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "spreadsheet",
        nargs="?",
        default=str(default_path),
        help="Path to the Excel spreadsheet to process (can be relative).",
    )
    args = parser.parse_args()
    return Path(args.spreadsheet)


if __name__ == "__main__":
    try:
        spreadsheet_path = _parse_args()
        asyncio.run(main(spreadsheet_path))
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting…", flush=True)