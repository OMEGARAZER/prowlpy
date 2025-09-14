# Prowlpy

[![PyPI Status](https://img.shields.io/pypi/status/prowlpy?logo=PyPI)](https://pypi.python.org/pypi/prowlpy)
[![PyPI version](https://img.shields.io/pypi/v/prowlpy.svg?logo=PyPI)](https://pypi.python.org/pypi/prowlpy)
[![Python Test](https://github.com/OMEGARAZER/prowlpy/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/OMEGARAZER/prowlpy/actions/workflows/test.yml)
[![linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&label=linting)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=Python)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Python library to interface with the [Prowl](https://www.prowlapp.com/) API.

## Installation

Prowlpy is installable as a library to be used within scripts or apps or with a CLI to send messages from the command line.

To install user/system wide use `pip install prowlpy` otherwise add it as normal to your pyproject.toml or requirements.txt

The CLI is not installed by default. You can include it when installing. Using [uv](https://github.com/astral-sh/uv) you would use this command:

```bash
uv tool install prowlpy[cli]
```

## Usage

Prowlpy can be used in multiple ways.

### library

#### Sync or Async

Both sync and async versions of the library are available. To use async, replace Prowl with AsyncProwl

#### Sending messages

```python
from prowlpy import Prowl

apikey = "1234567890123456789012345678901234567890"
p = Prowl(apikey=apikey)
p.send(application="Test App", event="Test Event", description="The testing event has failed")
```

Prowlpy can also be used within a context manager:

```python
from prowlpy import Prowl

apikey = "1234567890123456789012345678901234567890"
with Prowl(apikey=apikey) as p:
    p.send(application="Test App", event="Test Event", description="The testing event has failed")
```

#### Verify API key(s)

Prowlpy can also be used to verify an API key before sending a message or as a testing step like this:

```python
from prowlpy import Prowl

apikey = "1234567890123456789012345678901234567890"
p = Prowl(apikey=apikey)
p.verify_key()
```

If the key is not valid or an error occurs an APIError Exception will be raised.

#### Generate API Key(s)

Prowlpy can be used to generate API keys for users if you have a valid providerkey with a process similar to this:

```python
from prowlpy import Prowl

providerkey = "0987654321098765432109876543210987654321"
p = Prowl(providerkey=providerkey)
token_response = p.retrieve_token()
print(token_response["url"])
```

The user that the key is being created for will need to fillow the link provided and accept then the key can be created on the account with:

```python
...
apikey_respose = p.retrieve_apikey(token=token_response["token"])
print(apikey_response["apikey"])
```

### CLI

The CLI can be used to send massages via Prowl like this:

```bash
prowlpy --apikey="1234567890123456789012345678901234567890" --application="Test App" --event="Testing" --description="This is a test message"
```
