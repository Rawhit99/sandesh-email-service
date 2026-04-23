# sandesh-sdk

Official Python SDK for the Sandesh notification API.

## Install

```bash
pip install sandesh-sdk
```

## Quick start

```python
from sandesh.sdk import Sandesh

client = Sandesh(
    base_url="https://your-sandesh-api.example.com",
    bearer_token="your_jwt_or_api_key",
)

result = client.events_trigger(
    {
        "event": "user.welcome",
        "to": {"email": "user@example.com"},
        "payload": {"name": "Rohit"},
    }
)

print(result)
```

## Publish to PyPI

1. Build distribution files:

```bash
python -m pip install --upgrade build twine
python -m build
```

2. Validate package metadata:

```bash
python -m twine check dist/*
```

3. Upload to TestPyPI (recommended first):

```bash
python -m twine upload --repository testpypi dist/*
```

4. Upload to PyPI:

```bash
python -m twine upload dist/*
```

Set credentials using environment variables before uploading:

- `TWINE_USERNAME=__token__`
- `TWINE_PASSWORD=<your_pypi_api_token>`
