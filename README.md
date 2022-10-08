# calendar


## Features

* FastAPI
* SQLAlchemy and Alembic
* Pre-commit hooks (black, autoflake, isort, flake8, prettier)
* Github Action
* Dependabot config
* Docker images


## Notes

Implementation is not perfect. There are few things missing:
- Tests for api views
- Old events (that won't recur anymore in future) should be excluded from queries
-


## Step 1: Getting started

Start a local development instance with docker-compose

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Run database migration
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec backend alembic upgrade head

# Create database used for testing
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec postgres createdb apptest -U postgres
```

Now you can navigate to the following URLs:

- Backend OpenAPI docs: http://localhost:8000/docs/

There you can explore and play around with API.
Docs GUI is not always accurate, http://localhost:8000/api/v1/openapi.json is a better place to look for API constraints.


### Step 2: Setup pre-commit hooks and database

Keep your code clean by using the configured pre-commit hooks. Follow the [instructions here to install pre-commit](https://pre-commit.com/). Once pre-commit is installed, run this command to install the hooks into your git repository:

```bash
pre-commit install
```

### Local development

The backend setup of docker-compose is set to automatically reload the app whenever code is updated.

If you want to develop against something other than the default host, localhost:8000,
Don't forget to edit the `.env` file and update the `BACKEND_CORS_ORIGINS` value (add `http://mydomain:3000` to the allowed origins).


### Rebuilding containers

If you add a dependency, you'll need to rebuild your containers like this:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

### Database migrations


These two are the most used commands when working with alembic. For more info, follow through [Alembic's tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

```bash
# Auto generate a revision
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec backend alembic revision --autogenerate -m 'message'

# Apply latest changes
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec backend alembic upgrade head
```

### Backend tests

Backend uses a hardcoded database named apptest, first ensure that it's created

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec postgres createdb apptest -U postgres
```

Then you can run tests with this command:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml exec backend pytest --forked
```

TODO: find a way to run tests without `--forked`. Currently, `api` tests can't run along with `services` tests, as
`starlet` creates own event loop and breaks event loop used in `services`.
https://github.com/encode/starlette/issues/1315

## Recipes

#### Build and upload docker images to a repository

Configure the [**build-push-action**](https://github.com/marketplace/actions/build-and-push-docker-images) in `.github/workflows/test.yaml`.


## Credits

Created with [FastAPI Starter](https://github.com/gaganpreet/fastapi-starter)
