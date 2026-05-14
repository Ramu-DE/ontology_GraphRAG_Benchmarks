#!/usr/bin/env python3
"""Test Neptune connection with SSL workaround"""

from gremlin_python.driver import client, serializer
import ssl
import aiohttp

NEPTUNE_ENDPOINT = 'wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin'

print('Testing Neptune connection...')

# Create SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create aiohttp connector with custom SSL
connector = aiohttp.TCPConnector(ssl=ssl_context)

try:
    gremlin_client = client.Client(
        NEPTUNE_ENDPOINT,
        'g',
        message_serializer=serializer.GraphSONSerializersV2d0(),
        transport_factory=lambda: __import__('gremlin_python.driver.aiohttp.transport', fromlist=['AiohttpTransport']).AiohttpTransport(
            connector=connector
        )
    )

    result = gremlin_client.submit('g.V().limit(1).count()').all().result()
    print(f'✅ SUCCESS!')
    print(f'   Result: {result}')
    gremlin_client.close()

except Exception as e:
    print(f'❌ FAILED: {e}')
    import traceback
    traceback.print_exc()
