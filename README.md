# Sandesh - Email Notification System

A modern, production-ready email notification system with authentication, API key management, and comprehensive audit logging.

## Features

- 🔐 **User Authentication**: Secure login system with JWT tokens
- 🔑 **API Key Management**: Generate and manage API keys for programmatic access
- 📧 **Email Notifications**: Send templated emails via AWS SES
- 📊 **Audit Logging**: Track all email activities with detailed logs
- 🎨 **Modern UI**: Clean, minimal, and market-ready interface
- 🐳 **Docker Support**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- AWS account with SES configured
- Node.js 18+ (for local development)

### Using Docker Compose

1. **Clone the repository**
```bash
git clone <repository-url>
cd sandesh-first
```

2. **Configure environment variables**

Create a `.env` file in the root directory:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
SES_SENDER_EMAIL=no-reply@yourdomain.com
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### First Time Setup

1. **Register a new user**
   - Navigate to http://localhost:3000/login
   - Click "Sign up" to create a new account
   - Enter your username, password, and organization name

2. **Generate an API Key**
   - After logging in, go to "API Keys" in the sidebar
   - Click "Create API Key"
   - Copy and save the key immediately (you won't be able to see it again)

3. **Start sending emails**
   - Use your API key to send emails via the API
   - All activities will be logged in the "Audit Log" section

## API Usage

### Authentication

All API endpoints require authentication using either:
- JWT token (for UI access)
- API key (for programmatic access)

### Send an Email

```bash
curl -X POST http://localhost:8000/api/notifications \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "welcome_email",
    "email": "user@example.com",
    "payload": {
      "name": "John Doe",
      "company": "Acme Inc"
    }
  }'
```

### Create a Template

```bash
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "welcome_email",
    "name": "Welcome Email",
    "subject": "Welcome {{name}}!",
    "content": "<h1>Welcome {{name}}</h1><p>Thanks for joining {{company}}!</p>",
    "variables": {
      "name": "",
      "company": ""
    }
  }'
```

## Project Structure

```
sandesh-first/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   ├── models.py        # Database models
│   │   └── schemas.py       # Pydantic schemas
│   ├── middleware/
│   │   ├── auth.py          # Authentication middleware
│   │   └── auth_utils.py    # Auth utilities
│   ├── services/
│   │   ├── email_service.py # Email sending service
│   │   └── template_service.py # Template management
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # React components
│   │   └── services/        # API service
│   └── Dockerfile
└── docker-compose.yml
```

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Environment Variables

### Backend

- `DATABASE_URL`: PostgreSQL connection string
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `SES_SENDER_EMAIL`: Verified sender email
- `JWT_SECRET_KEY`: Secret used to sign console login JWTs. Set this in
  `.env` and use the same value in jwt.io for HS256 signature verification.
  If omitted in Docker Compose, the local fallback is
  `change-me-in-production`; replace it before deploying.

### Frontend

- `REACT_APP_API_URL`: Backend API URL

## Database Schema

### Users
- Stores user accounts and authentication data

### API Keys
- Stores API keys for programmatic access
- Keys are hashed before storage

### Audit Logs
- Tracks all email activities
- Includes payload, status, and metadata

### Notifications
- Email sending records
- Tracks status and errors

### Email Templates
- Reusable email templates
- Supports variables

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- API key hashing
- Audit logging for compliance
- IP address tracking
- User agent logging

## License

Licensed under the **MIT License**.

See **[LICENSE](./LICENSE)**.

## Repository Governance

- Contribution guidelines: **[CONTRIBUTING.md](./CONTRIBUTING.md)**
- Security reporting: **[SECURITY.md](./SECURITY.md)**
- Branch protection baseline:
  **[BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md)**
- Code of conduct: **[CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)**
- Support guide: **[SUPPORT.md](./SUPPORT.md)**

## Open source and PyPI publishing

Maintainers: see **[OPEN_SOURCE.md](./OPEN_SOURCE.md)** for a step-by-step plan to open source the project and publish the Python client/SDK to PyPI.

## Prebuilt Docker images (GHCR)

This repository publishes prebuilt images to GitHub Container Registry
using `.github/workflows/publish-images.yml`.

- Backend image:
  `ghcr.io/<owner>/<repo>-backend:<tag>`
- Frontend image:
  `ghcr.io/<owner>/<repo>-frontend:<tag>`

Published tags include:

- `latest` (latest main branch build)
- short commit SHA
- git tag (for example `v0.3.1`)

For your external compose repo, set:

- `SANDESH_BACKEND_IMAGE=ghcr.io/<owner>/<repo>-backend:latest`
- `SANDESH_FRONTEND_IMAGE=ghcr.io/<owner>/<repo>-frontend:latest`

## Support

For issues and questions, please open an issue on GitHub.

