
# Ask HN Digest

## Getting Started

All the information on how to run, develop and update your new application can be found in the documentation.

1. Update the name of the `.env.example` to `.env` and update relevant variables.

To start you'll need to run these commands:
1. `poetry install`
2. `poetry export -f requirements.txt --output requirements.txt --without-hashes`
3. `poetry run python manage.py makemigrations`
4. `make serve` : Make sure you have a Docker Engine running. I recommend OrbStack.

## Next steps
- When everything is running, go to http://localhost:8000/ to check if the backend is running.
  - If you get an error about manifest.json, just restart containers by doing Ctrl+C in the terminal and `make serve` again.
- You can sign up via regular signup. The first user will be made admin and superuser.
- Go to http://localhost:8000/admin/ and update Site info (http://localhost:8000/admin/sites/site/1/change/) to
  - localhost:8000 (if you are developing locally, and real domain when you are in prod)
  - Your project name


## Logfire
To start using Logfire, checkout their docs: https://logfire.pydantic.dev/docs/

It will be simple:
- Register
- Create a project
- Get a write token and add it to env vars in your prod environment


## Deployment

1. Create 4 apps on CapRover.
  - `ask_hn_digest`
  - `ask_hn_digest-workers`
  - `ask_hn_digest-postgres`
  - `ask_hn_digest-redis`

2. Create a new CapRover app token for:
   - `ask_hn_digest`
   - `ask_hn_digest-workers`

3. Add Environment Variables to those same apps from `.env`.

4. Create a new GitHub Actions secret with the following:
   - `CAPROVER_SERVER`
   - `CAPROVER_APP_TOKEN`
   - `WORKERS_APP_TOKEN`
   - `REGISTRY_TOKEN`

5. Then just push main branch.

## Notes
- Don't forget to update the site domain and name on the Admin Panel.
- If you made changes to tasks, you need to restart the worker container with `make restart-worker`.
- If you will need to use from `pgvector` don't forget to run `CREATE EXTENSION vector;` in your db, before running any migrations with `VectorFields`
