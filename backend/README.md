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

## Build compiled wheel (Cython)

To ship a binary wheel with Cython-compiled SDK modules, build with
`SANDESH_BUILD_COMPILED=1`.

Windows PowerShell:

```powershell
$env:SANDESH_BUILD_COMPILED="1"
python -m pip install --upgrade build cython
python -m build --wheel
```

Standard source + wheel build (default, no Cython compilation):

```powershell
Remove-Item Env:SANDESH_BUILD_COMPILED -ErrorAction Ignore
python -m build
```

Notes:

- Compiled wheels require a local C/C++ toolchain (for example, Microsoft
  C++ Build Tools on Windows).
- This raises reverse-engineering difficulty but cannot provide absolute code
  secrecy in Python packaging.

## IDE / Pylance types (`.pyi`)

Core modules may ship as compiled extensions (`.pyd`). Type checkers cannot
read those, so the package includes **stub files** (`*.pyi`) and `py.typed`
for autocomplete and static analysis (`EventApi`, `SubscriberApi`,
`SubscriberDto`, `Sandesh`, etc.).
