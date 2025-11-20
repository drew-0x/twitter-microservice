from threading import Thread

from uvicorn import Config


import logging
from fastapi import FastAPI

from src.grpc.server import serve

from src.dependencies.config import Config

from src.routes import router as TweetRouter

# OpenTelemetry Components
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# OpenTelementry istruments
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)

config = Config()


class App:
    def __init__(self) -> None:
        self.api: FastAPI = self.create_api()

    def startup_event(self):
        self.grpc_startup_event()
        print(f"Server initialized")

    def grpc_startup_event(self):
        # Start grpc
        grpc_thread = Thread(target=serve)
        grpc_thread.daemon = True
        grpc_thread.start()
        print("GRPC Initialized")

    def create_api(self):
        resource = Resource(attributes={"service.name": "tweet-service"})

        provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(endpoint=config["JAEGER"], insecure=True)

        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)

        app = FastAPI(on_startup=[self.startup_event])

        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        GrpcInstrumentorClient().instrument()
        GrpcInstrumentorServer().instrument()

        app.include_router(TweetRouter)

        return app


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
