#!/usr/bin/env python3
"""
CLI for managing candidate surveys

Example usage:
    poetry run candidate-surveys version

"""
import pathlib

import click
import dotenv

from candidate_surveys import commands


@click.group()
def cli() -> None:
    """Run cli commands"""
    dotenv.load_dotenv()


@cli.command()
def version() -> None:
    """Get the cli version."""
    click.echo(click.style("0.1.0", bold=True))


@cli.command()
@click.option(
    "--responses",
    default="responses.csv",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--config",
    default="config.json",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--logos",
    default="logos",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--output",
    default="output",
    type=click.Path(path_type=pathlib.Path),
)
def generate_pdfs(
    responses: pathlib.Path,
    config: pathlib.Path,
    logos: pathlib.Path,
    output: pathlib.Path,
) -> None:
    """Generate PDFs."""

    commands.generate_pdfs(
        responses,
        config,
        logos,
        output,
    )


if __name__ == "__main__":
    cli()
