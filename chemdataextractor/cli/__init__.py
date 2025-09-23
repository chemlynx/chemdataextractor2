"""
ChemDataExtractor command line interface.

Once installed, ChemDataExtractor provides a command-line tool that can be used
by typing 'cde' in a terminal for document extraction and processing.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from typing import BinaryIO
from typing import TextIO

import click

from .. import __version__
from ..doc import Document
import builtins

log = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose debug logging.")
@click.version_option(__version__, "--version", "-V")
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """ChemDataExtractor command line interface.

    Args:
        ctx: click.Context - Click context object
        verbose: bool - Enable verbose debug logging
    """
    log.debug(f"ChemDataExtractor v{__version__}")
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARN)
    ctx.obj = {}


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.File("w", encoding="utf8"),
    help="Output file.",
    default=click.get_text_stream("stdout"),
)
@click.argument("input", type=click.File("rb"), default=click.get_binary_stream("stdin"))
@click.pass_obj
def extract(ctx: builtins.dict[str, Any], input: BinaryIO, output: TextIO) -> None:
    """Run ChemDataExtractor on a document.

    Args:
        ctx: Dict[str, Any] - Click context object
        input: BinaryIO - Input file stream
        output: TextIO - Output file stream
    """
    log.info("chemdataextractor.extract")
    log.info(f"Reading {input.name}")
    doc = Document.from_file(input, fname=input.name)
    records = [record.serialize(primitive=True) for record in doc.records]
    jsonstring = json.dumps(records, indent=2, ensure_ascii=False)
    output.write(jsonstring)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.File("w", encoding="utf8"),
    help="Output file.",
    default=click.get_text_stream("stdout"),
)
@click.argument("input", type=click.File("rb"), default=click.get_binary_stream("stdin"))
@click.pass_obj
def read(ctx: builtins.dict[str, Any], input: BinaryIO, output: TextIO) -> None:
    """Output processed document elements.

    Args:
        ctx: Dict[str, Any] - Click context object
        input: BinaryIO - Input file stream
        output: TextIO - Output file stream
    """
    log.info("chemdataextractor.read")
    log.info(f"Reading {input.name}")
    doc = Document.from_file(input)
    for element in doc.elements:
        output.write(f"{element.__class__.__name__} : {str(element)}\n=====\n")


from . import cem
from . import chemdner
from . import cluster
from . import config
from . import data
from . import dict
from . import evaluate
from . import pos
from . import tokenize

cli.add_command(cluster.cluster_cli)
cli.add_command(config.config_cli)
cli.add_command(data.data_cli)
cli.add_command(tokenize.tokenize_cli)
cli.add_command(pos.pos_cli)
cli.add_command(chemdner.chemdner_cli)
cli.add_command(cem.cem)
cli.add_command(dict.dict_cli)
cli.add_command(evaluate.evaluate)
