"""Example to send notifications to multiple API keys through Prowl."""

import prowlpy

# it is recomended to use something like environs to avoid hardcoding keys
apikeys = [
    "1234567890123456789012345678901234567890",
    "0123456789012345678901234567890123456789",
    "9876543210987654321098765432109876543210",
    "0987654321098765432109876543210987654321",
]
prowl = prowlpy.Prowl(apikey=apikeys)
prowl.send(application="Test App", event="Test failed", description="The test has failed.", priority=1)
