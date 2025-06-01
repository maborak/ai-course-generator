import subprocess
import logging
from core.ports import FileConverterPort
import os

logger = logging.getLogger(__name__)

class FileConverter(FileConverterPort):
    def __init__(self, css_file="style.css"):
        logger.debug(f"Initializing FileConverter with css_file={css_file}")
        self.css_file = css_file

    def convert(self, md_file):
        base_name = os.path.splitext(md_file)[0]
        html_file = base_name + ".html"
        epub_file = base_name + ".epub"
        pdf_file = base_name + ".pdf"

        cmds = [
            ["pandoc", md_file, "-o", html_file, "--standalone", "--embed-resources", f"--css={self.css_file}", "--highlight-style=kate"],
            ["pandoc", md_file, "-o", epub_file, "--standalone", "--embed-resources", f"--css={self.css_file}", "--highlight-style=kate"],
            ["weasyprint", html_file, pdf_file]
        ]
        for cmd in cmds:
            logger.debug(f"Running command: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
                logger.debug(f"Command succeeded: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Command failed: {' '.join(cmd)} | Error: {e}")