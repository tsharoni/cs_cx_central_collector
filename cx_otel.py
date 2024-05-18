from os import environ

from opentelemetry import metrics
from opentelemetry.metrics import Observation, CallbackOptions
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

simulate = environ.get("simulate")

class CoralogixOtel:
    def __init__(self, endpoint, token):
        self.endpoint = endpoint
        self.token = token

        self.resource = Resource(attributes={SERVICE_NAME: "counter-metrics"})

        self.reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=endpoint,
                headers=[('authorization', "Bearer " + token)])
        )

        self.provider = MeterProvider(resource=self.resource, metric_readers=[self.reader])

        metrics.set_meter_provider(self.provider)


class CoralogixOtelGauge:

    def __init__(self, gauge_metric):
        def get_gauge_callback(_: CallbackOptions):
            yield Observation(self.value, self.attributes)

        self.gauge = metrics.get_meter(__name__).create_observable_gauge(
            callbacks=[get_gauge_callback],
            name=gauge_metric,
            description=gauge_metric,
            unit=""
        )

        self.value = 0
        self.attributes = {}

    def flush_results(self, cx_otel, labels, result):
        self.attributes = self.attributes | labels
        self.value = result
        print('Gauge: flushing labels:{} value: {}'.format(self.attributes, self.value))
        if (not simulate) or (simulate and simulate != '1' and simulate.lower() != 'true'):
            cx_otel.provider.force_flush()

        for label in labels:
            self.attributes.pop(label)

    def set_meta_attributes(self, attributes):
        self.attributes = attributes


class CoralogixOtelCounter:

    def __init__(self, counter_metric):

        self.counter = metrics.get_meter(__name__).create_counter(
            name=counter_metric,
            description=counter_metric)

        self.value = 0
        self.attributes = {}

    def counter_add(self, labels, result):
        self.attributes = self.attributes | labels
        self.value = result
        print('Counter: flushing labels:{} value: {}'.format(self.attributes, self.value))
        if simulate and simulate != 1 and simulate.lower != 'true':
            self.counter.add(self.value, self.attributes)

        for label in labels:
            self.attributes.pop(label)

    def set_meta_attributes(self, attributes):
        self.attributes = attributes
