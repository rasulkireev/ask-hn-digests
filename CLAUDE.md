# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup & Environment:**
```bash
# Initial setup
poetry install
poetry export -f requirements.txt --output requirements.txt --without-hashes
python manage.py makemigrations
make serve  # Starts Docker containers

# Environment setup
cp .env.example .env  # Update with your variables
```

**Development Server:**
```bash
make serve              # Start all services (Django, Redis, PostgreSQL, frontend)
make build              # Build Docker containers
make shell              # Django shell with shell_plus and IPython
make manage <command>   # Run Django management commands
```

**Database Operations:**
```bash
make makemigrations     # Create Django migrations
make migrate           # Apply migrations
```

**Frontend Development:**
```bash
npm run start          # Development server with hot reload
npm run build          # Production build
npm run watch          # Watch mode for development
```

**Testing & Code Quality:**
```bash
make test              # Run pytest
poetry run ruff check  # Lint Python code
poetry run ruff format # Format Python code
poetry run djlint .    # Lint Django templates
```

**Workers & Background Tasks:**
```bash
make restart-worker    # Restart Django-Q workers
```

## Architecture Overview

This is a Django-based web application that analyzes and summarizes Hacker News "Ask HN" discussions.

### Core Components

**Backend (Django):**
- `ask_hn_digest/` - Django project settings and configuration
- `core/` - Main application with models, views, tasks, and business logic
- Uses PostgreSQL with custom extensions for data storage
- Django-Q for background task processing
- Structured logging with structlog and Logfire integration

**Frontend:**
- Webpack-based build system with Stimulus.js controllers
- Templates in `frontend/templates/` with Django template inheritance
- Tailwind CSS for styling
- Bootstrap components integration

**Data Pipeline:**
- Async fetcher in `core/hn_utils.py` syncs Hacker News data
- AI-powered summarization using Google Gemini API
- Newsletter generation via Buttondown API
- Social media content creation for Twitter/Typefully

**Key Models:**
- `HNDiscussionSummary` - Core model storing analyzed discussions with summaries, titles, and social content
- `NewsletterSubscriber` - Email subscription management with Buttondown integration
- `Profile` - User profiles with unique keys
- `BlogPost` - CMS functionality for additional content

**Background Tasks (`core/tasks.py`):**
- `summarize_hn_discussion()` - Main AI summarization pipeline
- `sync_hn_data_async()` - Periodic HN data synchronization
- `generate_twitter_thread()` - Social media content generation
- `send_buttondown_newsletter()` - Email newsletter dispatch

### Services & Integrations

**External APIs:**
- Google Gemini for AI content generation
- Hacker News Firebase API for data fetching
- Buttondown for newsletter management
- Typefully for social media scheduling
- Sentry for error tracking
- Logfire for observability

**Storage & Infrastructure:**
- S3-compatible storage for media files
- WhiteNoise for static file serving
- Redis for Django-Q task queue
- Custom PostgreSQL image with vector extensions

## Development Guidelines

**Code Style:**
- No comments explaining obvious code (as per .cursor/rules/ai.mdc)
- No docstrings for functions
- Use structured logging with `get_ask_hn_digest_logger(__name__)`
- Follow existing patterns in neighboring files

**Dependencies:**
- Always use `poetry add <package>` instead of editing requirements.txt directly
- Regenerate requirements.txt with `poetry export -f requirements.txt --output requirements.txt --without-hashes`

**Logging Best Practices:**
- Use structured logging with consistent field names (user_id, email, profile_id)
- Include context: timing, request identifiers, business relevant data
- Never log secrets, tokens, or PII
- Use appropriate levels: INFO for business events, ERROR for failures

**Database:**
- Use Django ORM patterns established in the codebase
- Migrations are handled through standard Django workflow
- Models extend `BaseModel` for common timestamp fields

## Environment Configuration

The application expects a `.env` file based on `.env.example` with:
- Database credentials
- API keys (Gemini, Buttondown, Typefully, etc.)
- AWS/S3 configuration
- Sentry DSN for error tracking
- Various service endpoints

## Deployment

The application is designed for Docker deployment with separate containers for:
- Web server (`backend`)
- Background workers (`workers`)
- PostgreSQL database
- Redis for task queue
- Frontend asset serving

Production deployment uses CapRover with environment-specific configurations for logging, email backends, and external service integrations.
