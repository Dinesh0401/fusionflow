from __future__ import annotations

import json
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ..models import DecisionRecord

_gate_allow_counter = None
_gate_block_counter = None
_confidence_histogram = None
_risk_histogram = None
_tracer = None


def setup_telemetry(
    *,
    service_name: str,
    exporter_endpoint: Optional[str] = None,
    exporter_headers: Optional[str] = None,
) -> None:
    global _gate_allow_counter, _gate_block_counter, _confidence_histogram, _risk_histogram, _tracer

    resource = Resource(attributes={"service.name": service_name})

    if exporter_endpoint:
        span_exporter = OTLPSpanExporter(endpoint=exporter_endpoint, headers=_parse_headers(exporter_headers))
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer(__name__)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=exporter_endpoint, headers=_parse_headers(exporter_headers))
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        meter = metrics.get_meter(__name__)
    else:
        # no-op providers for local development
        _tracer = trace.get_tracer(__name__)
        meter = metrics.get_meter(__name__)

    _gate_allow_counter = meter.create_counter("gate.allow.count")
    _gate_block_counter = meter.create_counter("gate.block.count")
    _confidence_histogram = meter.create_histogram("llm.confidence", unit="1")
    _risk_histogram = meter.create_histogram("ml.risk", unit="1")


def _parse_headers(raw: Optional[str]) -> Optional[dict[str, str]]:
    if not raw:
        return None
    if raw.strip().startswith("{"):
        return json.loads(raw)
    headers: dict[str, str] = {}
    for part in raw.split(","):
        if not part:
            continue
        key, _, value = part.partition("=")
        if key and value:
            headers[key.strip()] = value.strip()
    return headers


def get_tracer():
    return _tracer or trace.get_tracer(__name__)


def record_gate_metrics(record: DecisionRecord) -> None:
    if _gate_allow_counter is None or _gate_block_counter is None:
        return

    attributes = {
        "provider": record.provider,
        "model": record.model,
        "prompt_hash": record.prompt_hash,
    }

    if (record.gate_verdict or "").lower() == "allow":
        _gate_allow_counter.add(1, attributes=attributes)
    else:
        _gate_block_counter.add(1, attributes=attributes)

    if record.llm_confidence is not None and _confidence_histogram is not None:
        _confidence_histogram.record(record.llm_confidence, attributes=attributes)

    if record.ml_risk_score is not None and _risk_histogram is not None:
        _risk_histogram.record(record.ml_risk_score, attributes=attributes)
*** End Patch