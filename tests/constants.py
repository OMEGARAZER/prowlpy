"""Constants for use in pytest testing."""

# Test keys
VALID_API_KEY: str = "0123456789abcdef0123456789abcdef01234567"
VALID_PROVIDER_KEY: str = "76543210fedcba9876543210fedcba9876543210"
VALID_TOKEN: str = "1234567890123456789012345678901234567890"

# Mock API responses
SUCCESS_RESPONSE: str = """<?xml version="1.0" encoding="UTF-8"?>
<prowl>
    <success code="200" remaining="994" resetdate="1234567890"/>
</prowl>"""

TOKEN_RESPONSE: str = """<?xml version="1.0" encoding="UTF-8"?>
<prowl>
    <success code="200" remaining="994" resetdate="1234567890"/>
    <retrieve token="1234567890123456789012345678901234567890"  url="https://www.prowlapp.com/retrieve.php?token=1234567890123456789012345678901234567890"/>
</prowl>"""

APIKEY_RESPONSE: str = """<?xml version="1.0" encoding="UTF-8"?>
<prowl>
    <success code="200" remaining="994" resetdate="1234567890"/>
    <retrieve apikey="0123456789abcdef0123456789abcdef01234567"/>
</prowl>"""

INVALID_XML_RESPONSE: str = """<?xml version="1.0" encoding="UTF-8"?>
<prowl>
    <invalid>Invalid XML structure</invalid>
</prowl>"""
