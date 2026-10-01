#!/usr/bin/env python3
"""Local smoke test: services -> UDP NetFlow v5 -> Elasticsearch -> Grafana."""
import base64
import json
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
config = json.loads(subprocess.check_output(
    ['docker', 'compose', 'config', '--format', 'json'], cwd=ROOT))
services = config['services']
es_env = services['elasticsearch']['environment']
gf_env = services['grafana']['environment']


def request(port, path, user, password, body=None):
    auth = base64.b64encode(f'{user}:{password}'.encode()).decode()
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}',
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def es(path, body=None):
    return request(9200, path, 'elastic', es_env['ELASTIC_PASSWORD'], body)


def grafana(path, body=None):
    return request(3000, path, gf_env['GF_SECURITY_ADMIN_USER'],
                   gf_env['GF_SECURITY_ADMIN_PASSWORD'], body)


def wait_for(check, label, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                print('OK:', label, flush=True)
                return result
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(2)
    raise SystemExit('FAIL: ' + label)


version = wait_for(lambda: es('/')['version']['number'], 'Elasticsearch HTTP')
assert version == services['elasticsearch']['image'].rsplit(':', 1)[1], version
wait_for(lambda: es('/_cluster/health')['status'] in ('yellow', 'green'), 'Elasticsearch cluster')
wait_for(lambda: request(5601, '/api/status', 'elastic', es_env['ELASTIC_PASSWORD'])
         ['status']['overall']['level'] == 'available', 'Kibana available')
health = wait_for(lambda: grafana('/api/health'), 'Grafana HTTP')
assert health['database'] == 'ok', health
assert health['version'] == services['grafana']['image'].rsplit(':', 1)[1], health
uid = 'aeznn8invxnggb'
wait_for(lambda: grafana('/api/dashboards/uid/fff4a0e1-5179-4224-b3bc-8377fc6fcdb3'),
         'Dashboard provisioned')

# One v5 flow: documentation-only IPs, 10 packets, 1200 bytes, UDP/443.
source_port = secrets.randbelow(20000) + 40000
now = int(time.time())
header = struct.pack('!HHIIIIBBH', 5, 1, 60000, now, 0, 1, 0, 0, 0)
record = struct.pack('!4s4s4sHHIIIIHHBBBBHHBBH',
    socket.inet_aton('192.0.2.10'), socket.inet_aton('198.51.100.20'), b'\0'*4,
    1, 2, 10, 1200, 59000, 60000, source_port, 443,
    0, 0, 17, 0, 64512, 64513, 24, 24, 0)
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.sendto(header + record, ('127.0.0.1', 2055))
query = {'query': {'bool': {'filter': [
    {'term': {'source.ip': '192.0.2.10'}},
    {'term': {'source.port': source_port}},
    {'range': {'@timestamp': {'gte': now * 1000 - 2000}}}
]}}}
hits = wait_for(lambda: es('/filebeat-*/_search', query)['hits']['hits'],
                'NetFlow v5 received and indexed', 90)
event = hits[0]['_source']
assert event['destination']['ip'] == '198.51.100.20', event
assert event['network']['bytes'] == 1200, event
assert event['network']['packets'] == 10, event
wait_for(lambda: grafana(f'/api/datasources/uid/{uid}/health')['status'] == 'OK',
         'Grafana datasource health')
result = grafana('/api/ds/query', {
    'from': str((now - 60) * 1000), 'to': str((now + 60) * 1000),
    'queries': [{
        'refId': 'A', 'datasource': {'type': 'elasticsearch', 'uid': uid},
        'query': f'source.ip:"192.0.2.10" AND source.port:{source_port}',
        'timeField': '@timestamp', 'metrics': [{'id': '1', 'type': 'count'}],
        'bucketAggs': [{'id': '2', 'type': 'date_histogram', 'field': '@timestamp',
                        'settings': {'interval': '10s', 'min_doc_count': '0'}}],
        'intervalMs': 10000, 'maxDataPoints': 100,
    }],
})
answer = result['results']['A']
assert not answer.get('error'), answer
counts = [value for frame in answer.get('frames', [])
          for field, values in zip(frame['schema']['fields'], frame['data']['values'])
          if field['type'] == 'number' for value in values if value is not None]
assert sum(counts) >= 1, 'Grafana query did not return the test flow'
print('OK: flow queried through Grafana datasource; Elastic', version,
      '/ Grafana', health['version'])
