import logging
logger = logging.getLogger(__name__)

class AITipsGenerator:
    def __init__(self, engine, converter):
        logger.debug(f"Initializing AITipsGenerator with engine={engine.__class__.__name__}, converter={converter.__class__.__name__}")
        self.engine = engine
        self.converter = converter

    def generate_tips(self, topic, quantity, output_md, force=False):
        import os

        logger.debug(f"generate_tips called with topic={topic}, quantity={quantity}, output_md={output_md}, force={force}")
        if os.path.exists(output_md) and not force:
            logger.warning(f"File '{output_md}' already exists. Use --force to overwrite.")
            print(f"File '{output_md}' already exists. Use --force to overwrite.")
            return

        logger.debug(f"Calling engine.generate()...")
        tips = self.engine.generate(topic, quantity)

        def format_tips_to_markdown(tips_list):
            md = ""
            for idx, tip_title, tip_detail in tips_list:
                md += f"## Tip #{idx}: {tip_title}\n\n{tip_detail}\n\n***\n"
            return md

        if isinstance(tips, str):
            text = tips
        else:
            text = format_tips_to_markdown(tips)
        logger.debug(f"Writing generated tips to {output_md}")

        with open(output_md, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Markdown saved as {output_md}")

        logger.debug("Calling converter.convert()...")
        self.converter.convert(output_md)
        logger.info("File conversion complete.")

    def format_tips_to_markdown(self, tips_list):
        md = ""
        for idx, tip_title, tip_detail in tips_list:
            md += f"### Tip #{idx}: {tip_title}\n\n{tip_detail}\n\n***\n"
        return md