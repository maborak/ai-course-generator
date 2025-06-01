import logging
from core.ports import CompletionEnginePort

logger = logging.getLogger(__name__)

class OllamaEngine(CompletionEnginePort):
    def __init__(self, model, host=None, stream=False):
        import ollama
        logger.debug(f"Initializing OllamaEngine with model={model}, host={host}, stream={stream}")
        self.ollama = ollama
        self.model = model
        self.host = host
        self.stream = stream

    def generate(self, prompt, quantity):
        logger.debug(f"Generating tips with OllamaEngine. Prompt: {prompt[:100]}..., Quantity: {quantity}")
        kwargs = {}
        if self.host:
            kwargs['host'] = self.host
        if self.stream:
            logger.debug("OllamaEngine using streaming mode")
            stream_response = self.ollama.chat(model=self.model, messages=[{"role":"user", "content":prompt}], stream=True, **kwargs)
            result = ""
            for msg in stream_response:
                logger.debug(f"OllamaEngine stream message: {msg['message']['content'][:50]}...")
                result += msg['message']['content']
            logger.debug(f"OllamaEngine full streaming response: {result[:100]}...")
            return result
        else:
            response = self.ollama.chat(model=self.model, messages=[{"role":"user", "content":prompt}], **kwargs)
            result = response['message']['content']
            logger.debug(f"OllamaEngine response: {result[:100]}...")
            return result