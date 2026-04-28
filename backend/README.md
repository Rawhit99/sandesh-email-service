# sandesh-sdk

Official Python SDK for the Sandesh notification API.

## License

This SDK is licensed under the **MIT License**.

See `../LICENSE`.

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
        "name": "vendor-assessment-form-to-vendor",
        "to": {"subscriberId": "vendor-contact-1"},
        "payload": {
            "organisation": "Acme Corp",
            "vendor_name": "Globex",
            "assessment_name": "Vendor Risk Check",
            "due_date": "April 30, 2026",
            "url": "https://app.example.com/assessment?id=123",
        },
        "overrides": {
            "email": {
                "cc": ["risk@example.com"],
                "subject": "Reminder: Vendor Risk Check",
            }
        },
    }
)

print(result)
```

## Covered methods

- Events: strict and legacy trigger methods.
- Subscribers: create/get/list/update/deactivate.
- Notifications: create/list/get/seen/unseen/retry/resend.
- Templates: list/create/get/update/delete/preview/validate.
- Integrations and credentials.
- Settings, SES helpers, stats, and health.


If your code currently uses Novu-style classes, switch imports only:

```python
from sandesh.api import EventApi, SubscriberApi
from sandesh.dto import SubscriberDto
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
