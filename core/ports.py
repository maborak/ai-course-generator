import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class CompletionEnginePort(ABC):
    @abstractmethod
    def generate(self, topic, quantity):
        pass


class FileConverterPort(ABC):
    @abstractmethod
    def convert(self, md_file):
        pass