#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

"""
File converter implementation for AI Tips Generator.

Provides a concrete implementation of FileConverterPort for converting markdown files
to HTML, EPUB, and PDF using Pandoc and WeasyPrint.
"""

import os
from pathlib import Path
import subprocess
import logging
from typing import Optional
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
        self._themes_dir = self._get_themes_dir()
        self.css_file = self._get_css_path(theme)

    @staticmethod
    def _get_themes_dir() -> Path:
        """Get the path to the themes directory.

        Returns:
            Path: Path to the themes directory.

        Raises:
            FileNotFoundError: If themes directory doesn't exist.
        """
        themes_dir = Path(__file__).parent.parent / "themes"
        if not themes_dir.exists():
            raise FileNotFoundError(f"Themes directory not found at {themes_dir}")
        return themes_dir

    def _get_default_css_path(self) -> str:
        """Get the path to the default CSS file.

        Returns:
            str: Path to the default CSS file.
        """
        return str(self._themes_dir / "default.css")

    def _get_css_path(self, theme: str) -> str:
        """Get the path to the CSS file for the specified theme.

        Args:
            theme (str): Name of the theme to use.

        Returns:
            str: Path to the CSS file.
        """
        if theme == "default":
            return self._get_default_css_path()
        
        css_path = self._themes_dir / f"{theme}.css"
        
        if not css_path.exists():
            logger.warning("Theme '%s' not found, falling back to default theme", theme)
            return self._get_default_css_path()
        
        return str(css_path)

    def convert(self, md_file: str, metadata: Optional[dict] = None, force: bool = False) -> None:
        """Convert a markdown file to HTML, EPUB, and PDF formats.

        Args:
            md_file (str): Path to the markdown file to convert.
            metadata (dict, optional): Metadata to embed in the output files.
            force (bool): Whether to force overwrite existing files.
        """
        if metadata is None:
            metadata = {}
            
        # Get the directory of the input markdown file
        md_path = Path(md_file)
        output_dir = md_path.parent
            
        base_name = md_path.stem
        output_files = {
            'html': str(output_dir / f"{base_name}.html"),
            'epub': str(output_dir / f"{base_name}.epub"),
            'pdf': str(output_dir / f"{base_name}.pdf")
        }

        # Check if output files exist and handle force flag
        for output_file in output_files.values():
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
                "pandoc", md_file, "-o", output_files['html'], "--standalone",
                "--embed-resources", f"--css={self.css_file}",
                "--highlight-style=kate"
            ],
            [
                "pandoc", md_file, "-o", output_files['epub'], "--standalone",
                "--embed-resources", f"--css={self.css_file}",
                "--highlight-style=kate"
            ] + meta_args,
            ["weasyprint", output_files['html'], output_files['pdf']]
        ]
        
        for cmd in cmds:
            logger.info("Running command: %s", ' '.join(cmd))
            try:
                subprocess.run(cmd, check=True)
                logger.info("Command succeeded: %s", ' '.join(cmd))
            except subprocess.CalledProcessError as exc:
                logger.error("Command failed: %s | Error: %s", ' '.join(cmd), exc)
