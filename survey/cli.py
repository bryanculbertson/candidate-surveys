#!/usr/bin/env python3
"""
CLI for managing candidate surveys

Example usage:
    poetry run survey version

"""
from typing import Any

import click
import dotenv

from . import pdf_tools


@click.group()
def cli() -> None:
    """Run cli commands"""
    dotenv.load_dotenv()


@cli.command()
def version() -> None:
    """Get the cli version."""
    click.echo(click.style("0.1.0", bold=True))


@cli.command()
@click.argument("csv_filename")
@click.argument("config_filename")
@click.argument("logo_directory")
@click.argument("output_directory")
def generate_pdfs(args: Any) -> None:
    """Generate PDFs."""

    pdf_tools.run(args)


if __name__ == "__main__":
    cli()
