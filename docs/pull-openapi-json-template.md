# IoTConnect REST API — OpenAPI Specifications

This directory contains the OpenAPI (Swagger) specifications for the IoTConnect REST API,
one JSON file per physical microservice.

You can use these spect to inform your coding agents about how to use the /IOTCONNECT API.
Based on these spects, you can extend this library's functionaluty. 

* `docs/pull-openapi-json-template.md` is a template used as input to the script below.
* `work/schemas/RADME.md` is a Generated file.

To generate work/schemas/RADME.md, execute the script `docs/pull-openapi-json.py`:
```bash
 export IOTC_ENV=poc # your environment
 export IOTC_PF=aws # your platform, though at this time azure does not support openapi specs
 export IOTC_SKEY='MkQ3NjgxNzct...dkDKeM' #your actual solution key here
python3 -m pip install requests
python3 docs/pull-openapi-json.py
```

## How the API is organized

Each `*.json` file describes one physical microservice, reachable at a base URL of the form
`https://<host>/api/v2.1`. Discovery (the service that hands out these URLs) commonly maps
**several top-level service names onto the same base URL** — they are aliases for one physical
microservice rather than separate servers.

The Services table below lists, for each fetched spec, all of the top-level service names that
discovery associates with its base URL, and the spec file that documents it.

## Authentication

Every service **except the authentication service** requires a bearer token.

1. **Obtain a token** from the **auth** service (`https://<auth-host>/api/v2.1`):
   - `POST /Auth/login` — log in with credentials to receive an `access_token` and a refresh token.
   - `POST /Auth/refresh-token` — exchange a refresh token for a fresh `access_token` (tokens expire).
   - `GET /Auth/verify-token` — check whether an access token is still valid.
2. **Use the token** on every other service by sending this HTTP header with each request:

   ```
   Authorization: Bearer <access_token>
   ```

Calls to any non-auth service without a valid token return `401 Unauthorized`. Each service's own
OpenAPI description repeats this requirement; it is stated once here so the per-service specs can be
read without rediscovering it.

## Services

@@@SERVICES_TABLE@@@
