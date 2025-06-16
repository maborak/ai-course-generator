#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

"""
File converter implementation for AI Tips Generator.

Provides a concrete implementation of FileConverterPort for converting markdown files
to HTML, EPUB, and PDF using Pandoc and WeasyPrint.
"""

import os
import subprocess
import logging
from core.ports import FileConverterPort

logger = logging.getLogger(__name__)

class FileConverter(FileConverterPort):
    """Converts markdown files to HTML, EPUB, and PDF formats."""
    def __init__(self, css_file: str = "style.css"):
        """Initialize the FileConverter.

        Args:
            css_file (str): Path to the CSS file for styling output.
        """
        logger.debug("Initializing FileConverter with css_file=%s", css_file)
        self.css_file = css_file

    def convert(self, md_file: str, metadata: dict = None, force: bool = False) -> None:
        """Convert a markdown file to HTML, EPUB, and PDF formats.

        Args:
            md_file (str): Path to the markdown file to convert.
            metadata (dict, optional): Metadata to embed in the output files.
        """
        if metadata is None:
            metadata = {}

        base_name = os.path.splitext(md_file)[0]
        html_file = base_name + ".html"
        epub_file = base_name + ".epub"
        pdf_file = base_name + ".pdf"

        # Prepare metadata arguments for Pandoc
        meta_args = []
        for key, value in metadata.items():
            meta_args.extend(["--metadata", f"{key}={value}"])

        cmds = [
            [
                "pandoc", md_file, "-o", html_file, "--standalone",
                "--embed-resources", f"--css={self.css_file}",
                "--highlight-style=kate"
            ],
            [
                "pandoc", md_file, "-o", epub_file, "--standalone",
                "--embed-resources", f"--css={self.css_file}",
                "--highlight-style=kate"
            ] + meta_args,
            ["weasyprint", html_file, pdf_file]
        ]
        for cmd in cmds:
            print("Running command: %s", ' '.join(cmd))
            try:
                subprocess.run(cmd, check=True)
                print("Command succeeded: %s", ' '.join(cmd))
            except subprocess.CalledProcessError as exc:
                print("Command failed: %s | Error: %s", ' '.join(cmd), exc)
