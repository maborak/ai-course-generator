import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AITipsGenerator:
    def __init__(self, engine, converter):
        logger.debug(f"Initializing AITipsGenerator with engine={engine.__class__.__name__}, converter={converter.__class__.__name__}")
        self.engine = engine
        self.converter = converter
        self.tokens_used = 0

    def generate_tips(self, topic, quantity, output_md, force=False):
        start_time = time.time()
        logger.info(f"Generating {quantity} tips for topic '{topic}'")
        tips = self.engine.generate_tip_titles(topic, quantity)
        details = []
        for i, tip in enumerate(tips, 1):
            detail = self.engine.generate_tip_detail(topic, tip["full"], i, len(tips))
            details.append((i, tip, detail))
        elapsed = time.time() - start_time

        # Add expertise level, category, model, generation time, date, and tokens to the top of the markdown
        expertise_level = getattr(self.engine, "expertise_level", "Unknown")
        category = getattr(self.engine, "category", "Unknown")
        model = getattr(self.engine, "model", "Unknown")
        tokens_used = getattr(self.engine, "tokens_used", "Unknown")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"# {topic} ({category})\n\n"
            f"---\n\n"
            f"## Document Info\n\n"
            f"- **Expertise Level:** {expertise_level}\n"
            f"- **Category:** {category}\n"
            f"- **Model Used:** {model}\n"
            f"- **Total Tokens Used:** {tokens_used}\n"
            f"- **Generated on:** {now_str}\n"
            f"- **Generated in:** {elapsed:.2f} seconds\n\n"
            "---\n\n"
        )

        with open(output_md, "w", encoding="utf-8") as f:
            f.write(header)
            for i, tip, detail in details:
                f.write(f"## {i}. {tip['full']}\n")
                f.write(f"**Short Title:** {tip['short']}\n\n")
                f.write(detail.strip() + "\n\n---\n\n")
        logger.info(f"Markdown saved as {output_md}")
        logger.info(f"Total tokens used: {tokens_used}")

        self.converter.convert(output_md)

    def format_tips_to_markdown(self, tips_list):
        md = ""
        for idx, tip_title, tip_detail in tips_list:
            md += f"### Tip #{idx}: {tip_title}\n\n{tip_detail}\n\n***\n"
        return md