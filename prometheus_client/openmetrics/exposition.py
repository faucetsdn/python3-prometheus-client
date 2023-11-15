#!/usr/bin/env python


from ..utils import floatToGoString

CONTENT_TYPE_LATEST = 'application/openmetrics-text; version=0.0.1; charset=utf-8'
"""Content type of the latest OpenMetrics text format"""


def _is_valid_exemplar_metric(metric, sample):
    if metric.type == 'counter' and sample.name.endswith('_total'):
        return True
    if metric.type in ('histogram', 'gaugehistogram') and sample.name.endswith('_bucket'):
        return True
    return False


def generate_latest(registry):
    '''Returns the metrics from the registry in latest text format as a string.'''
    output = []
    for metric in registry.collect():
        try:
            mname = metric.name
            output.append('# HELP {} {}\n'.format(
                mname, metric.documentation.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"')))
            output.append(f'# TYPE {mname} {metric.type}\n')
            if metric.unit:
                output.append(f'# UNIT {mname} {metric.unit}\n')
            for s in metric.samples:
                if s.labels:
                    labelstr = '{{{0}}}'.format(','.join(
                        ['{}="{}"'.format(
                            k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                            for k, v in sorted(s.labels.items())]))
                else:
                    labelstr = ''
                if s.exemplar:
                    if not _is_valid_exemplar_metric(metric, s):
                        raise ValueError(f"Metric {metric.name} has exemplars, but is not a histogram bucket or counter")
                    labels = '{{{0}}}'.format(','.join(
                        ['{}="{}"'.format(
                            k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                            for k, v in sorted(s.exemplar.labels.items())]))
                    if s.exemplar.timestamp is not None:
                        exemplarstr = ' # {} {} {}'.format(
                            labels,
                            floatToGoString(s.exemplar.value),
                            s.exemplar.timestamp,
                        )
                    else:
                        exemplarstr = ' # {} {}'.format(
                            labels,
                            floatToGoString(s.exemplar.value),
                        )
                else:
                    exemplarstr = ''
                timestamp = ''
                if s.timestamp is not None:
                    timestamp = f' {s.timestamp}'
                output.append('{}{} {}{}{}\n'.format(
                    s.name,
                    labelstr,
                    floatToGoString(s.value),
                    timestamp,
                    exemplarstr,
                ))
        except Exception as exception:
            exception.args = (exception.args or ('',)) + (metric,)
            raise

    output.append('# EOF\n')
    return ''.join(output).encode('utf-8')
