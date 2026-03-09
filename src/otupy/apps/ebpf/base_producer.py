from abc import ABC, abstractmethod

class BaseEBPFProducer(ABC):

    @abstractmethod
    def load(self, producer, target, asset_id: str):
        pass

    @abstractmethod
    def delete(self, producer, target, asset_id: str):
        pass

    @abstractmethod
    def query(self, producer, target, asset_id: str):
        pass