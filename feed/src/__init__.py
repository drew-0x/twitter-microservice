import logging
from fastapi import FastAPI

from src.dependencies.config import Config

from src.routes import router as FeedRouter

# OpenTelemetry Components
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# OpenTelemetry instruments
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

config = Config()


class App:
    def __init__(self) -> None:
        self.api: FastAPI = self.create_api()

    def startup_event(self):
        print("Feed service initialized")

    def create_api(self):
        resource = Resource(attributes={"service.name": "feed-service"})

        provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(endpoint=config["JAEGER"], insecure=True)

        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)

        app = FastAPI(on_startup=[self.startup_event])

        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        GrpcInstrumentorClient().instrument()

        app.include_router(FeedRouter)

        return app


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
