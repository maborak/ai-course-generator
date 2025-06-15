#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File conversion verification module for AI Tips Generator.

This module provides functionality to verify that file conversions
are working correctly by testing with dummy content.
"""

import os
import tempfile
import logging
from typing import Dict
from adapters.file_converter import FileConverter

logger = logging.getLogger(__name__)

class FileConversionVerifier:
    """Verifies that file conversions are working correctly."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the FileConversionVerifier.
        
        Args:
            output_dir (str): Directory where test files will be created
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def verify(self) -> Dict[str, bool]:
        """Verify that all file conversions work correctly.
        
        Returns:
            Dict[str, bool]: Dictionary mapping file extensions to success status
        """
        # Create dummy content
        dummy_content = '''# Dummy AI Tips Output

This is a test file for verification mode.

## Tip 1
Dummy tip content.

## Tip 2
More dummy content.
'''

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            dir=self.output_dir, prefix="check_", suffix="_tip.md", delete=False
        ) as tmp_md:
            output_md = tmp_md.name
            tmp_md.write(dummy_content.encode("utf-8"))
        logger.info("Dummy markdown saved as %s", output_md)

        # Convert files
        converter = FileConverter()
        try:
            converter.convert(output_md)
        except Exception as exc:
            logger.error("Failed to convert files: %s", exc)
            return {ext: False for ext in [".md", ".html", ".pdf", ".epub"]}

        # Check results
        base = os.path.splitext(output_md)[0]
        results = {}
        for ext in [".md", ".html", ".pdf", ".epub"]:
            file_path = base + ext
            results[ext] = os.path.exists(file_path)

        # Cleanup
        for ext in [".md", ".html", ".pdf", ".epub"]:
            file_path = base + ext
            if os.path.exists(file_path):
                os.remove(file_path)

        return results
