#!/usr/bin/env python3
"""
CLI for managing candidate surveys

Example usage:
    poetry run survey version

"""
from typing import Any

import click
import dotenv

from survey import commands


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

    commands.generate_pdfs(
        args.csv_filename,
        args.config_filename,
        args.logo_directory,
        args.output_directory,
    )


if __name__ == "__main__":
    cli()
