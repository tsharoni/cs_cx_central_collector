
import cx_otel
import random
import time
from os import environ

if __name__ == '__main__':

    try:
    # set one time the otel provider, by variables
        otel_provider = cx_otel.CoralogixOtel(
            environ.get('CX_ENDPOINT'),
            environ.get("CX_TOKEN"))
    except:
    # or by the otel collector agent (no need to set the key)
        otel_provider = cx_otel.CoralogixOtel(
            'http://localhost:4317/',
            'token is handled by agent')

    # set 2 gauges
    gauge1 = cx_otel.CoralogixOtelGauge('gauge_test1')
    gauge2 = cx_otel.CoralogixOtelGauge('Gauge2')

    # set meta fields and flush results for each of the gauges
    gauge1.set_meta_attributes({'meta1':'value1', 'meta2': 'value2'})
    gauge1.flush_results(otel_provider, {'attr1': 'value3', 'attr2': 'value4'}, 2)

    gauge2.set_meta_attributes({'meta1': 'value1', 'meta2': 'value2'})
    gauge2.flush_results(otel_provider, {'attr1': 'value3'}, 22)

    # set 2 counters and set meta fields

    counter1 = cx_otel.CoralogixOtelCounter('counter_test')
    counter1.set_meta_attributes({'meta1': 'value1'})
    counter2 = cx_otel.CoralogixOtelCounter('counter2')
    counter2.set_meta_attributes({'meta1': 'value1'})

    # increase counters (every 30 seconds)
    for x in range(0, 0):
        counter1.counter_add({'counter1': 'value1'}, random.randint(1, 10))
        counter2.counter_add({'counter2': 'value2'}, random.randint(1, 10))
        time.sleep(30)
