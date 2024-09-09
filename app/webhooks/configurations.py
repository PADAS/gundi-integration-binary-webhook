from datetime import datetime

from .core import GenericJsonTransformWithHexStrConfig, GenericJsonWithHexStrPayload


class BinaryWebhookPayload(GenericJsonWithHexStrPayload):
    device: str
    time: datetime
    data: str
    seqNumber: int
    ack: bool



class BinaryWebhookConfig(GenericJsonTransformWithHexStrConfig):
    pass
