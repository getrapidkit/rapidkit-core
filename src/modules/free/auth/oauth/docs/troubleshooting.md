# OAuth Module Troubleshooting

## Missing Client Credentials

**Symptom**: Authorisation redirect fails with `invalid_client`.

**Fix**: Ensure `client_id` and `client_secret` are loaded from your secrets manager and injected
into the provider registry before redirecting users.

## Invalid Redirect URI

**Symptom**: Provider shows `redirect_uri_mismatch`.

**Fix**: Confirm the callback URL configured with the provider exactly matches the one produced by
`build_authorize_url()` including protocol and trailing slash.

## State Validation Errors

**Symptom**: Callback handler rejects the request with `state mismatch`.

**Fix**: Persist state tokens between the initial redirect and the callback (for example using the
session module). Ensure the same key is used when generating and validating the state parameter.

## Token Exchange Fails

**Symptom**: Token endpoint returns HTTP 4xx or 5xx.

**Fix**: Log the request payload produced by `token_request_payload()` and compare it with the
provider documentation. Typical culprits are missing `code_verifier` (for PKCE) or incorrect
`redirect_uri`.

Run `poetry run pytest tests/modules/free_auth_oauth -q` after amending provider logic to catch
regressions early.
