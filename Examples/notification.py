"""Example to send notifications through Prowl."""

import prowlpy

# it is recomended to use something like environs to avoid hardcoding keys
apikey = "1234567890123456789012345678901234567890"
prowl = prowlpy.Prowl(apikey=apikey)
prowl.send(application="Test App", event="Test failed", description="The test has failed.", priority=1)
