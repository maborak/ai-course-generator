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
    def __init__(self, theme: str = "normal"):
        """Initialize the FileConverter.

        Args:
            theme (str): Name of the theme to use for styling output.
        """
        logger.debug("Initializing FileConverter with theme=%s", theme)
        self.theme = theme
        self.css_file = self._get_css_path(theme)

    def _get_css_path(self, theme: str) -> str:
        """Get the path to the CSS file for the specified theme.

        Args:
            theme (str): Name of the theme to use.

        Returns:
            str: Path to the CSS file.
        """
        if theme == "default":
            return "default.css"
        
        themes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes")
        css_path = os.path.join(themes_dir, f"{theme}.css")
        
        if not os.path.exists(css_path):
            logger.warning("Theme '%s' not found, falling back to default theme", theme)
            return "default.css"
        
        return css_path

    def convert(self, md_file: str, metadata: dict = None, force: bool = False) -> None:
        """Convert a markdown file to HTML, EPUB, and PDF formats.

        Args:
            md_file (str): Path to the markdown file to convert.
            metadata (dict, optional): Metadata to embed in the output files.
            force (bool): Whether to force overwrite existing files.
        """
        if metadata is None:
            metadata = {}
        base_name = os.path.splitext(md_file)[0]
        html_file = base_name + ".html"
        epub_file = base_name + ".epub"
        pdf_file = base_name + ".pdf"

        # Check if output files exist and handle force flag
        for output_file in [html_file, epub_file, pdf_file]:
            if os.path.exists(output_file) and not force:
                logger.error("Output file already exists: %s", output_file)
                logger.error("Use --force to overwrite existing file")
                return

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
