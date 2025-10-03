import asyncio
import functools
import logging
import ssl

import aiohttp
import jwt
import retry

logger = logging.getLogger("app.oauth2")


class OAuth2TokenHandler:
    def __init__(
            self,
            authorizer_url: str,
            client_id: str,
            client_secret: str,
            extra_scopes: list[str] | None = None,
            skip_ssl=False,
    ) -> None:
        self._authorizer_url = authorizer_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._request_payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }
        if isinstance(extra_scopes, list) and len(extra_scopes) > 0:
            self._request_payload["scope"] = functools.reduce(lambda a, b: f"{a} {b}", extra_scopes)
        self._refresh_token_payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": None,
        }
        self._validate_ssl = not skip_ssl

        self._renew_task: asyncio.Task | None = None
        self._renew_callback = None

    @retry.retry(exceptions=Exception, tries=3, delay=1, max_delay=3, logger=logger)
    async def _make_post_request(self, payload: dict):
        logger.debug(f'Making POST {self._authorizer_url}, grant_type = {payload.get("grant_type")}')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self._authorizer_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data=payload,
                    ssl=self._validate_ssl,
            ) as r:
                response = await r.json()
                # logger.debug(f'Got {response}')
                return response

    async def request_token(self, auto_renew=False, renew_callback=None) -> dict:
        logger.info(f'Requesting token for client {self._client_id}')
        token = await self._make_post_request(self._request_payload)
        assert "error" not in token, f'Cannot get OAuth2 token! {token.get("error_description") or token.get("error")}'

        if auto_renew:
            self._renew_callback = renew_callback
            self._renew_task = asyncio.create_task(self._auto_renew_task(token))
            self._renew_task.add_done_callback(self._auto_renew_task_done_cb)

        return token

    async def _auto_renew_task(self, token: dict):
        try:
            logger.info("Starting token auto-renew task")

            retry_renew_callback = retry.retry(
                exceptions=Exception, tries=3, delay=1, max_delay=3, logger=logger
            )(self._renew_callback)

            while True:
                token_expiration = token["expires_in"]
                if token_expiration < 10:
                    token_expiration = 13
                has_refresh_token = "refresh_token" in token
                refresh_expiration = token.get("refresh_expires_in", 1000000000)
                if refresh_expiration < 10:
                    refresh_expiration = 13

                if has_refresh_token:
                    sleep_seconds = min(token_expiration, refresh_expiration) - 10
                else:
                    sleep_seconds = token_expiration - 10

                logger.debug(f"Sleeping for {sleep_seconds} seconds")
                await asyncio.sleep(sleep_seconds)
                try:
                    if not has_refresh_token:
                        # No refresh token, simply renew it!
                        new_token = await self._make_post_request(self._request_payload)
                        assert "error" not in new_token, (
                            f'Cannot get OAuth2 token! {new_token.get("error_description") or new_token.get("error")}'
                        )
                    else:
                        # Got also a refresh token, try to renew using it
                        self._refresh_token_payload["refresh_token"] = token["refresh_token"]
                        try:
                            new_token = await self._make_post_request(self._refresh_token_payload)
                            assert "error" not in new_token
                        except Exception:
                            logger.warning("Cannot refresh token! Trying requesting a new one")
                            new_token = await self._make_post_request(self._request_payload)
                            assert "error" not in new_token, f'Cannot get OAuth2 token! {new_token.get("error_description")}'

                    token = new_token
                    await retry_renew_callback(token)
                except Exception:
                    logger.exception('Cannot get an updated OAuth2 token! Will retry in 10 seconds')
                    if isinstance(token, dict):
                        token = {"expires_in": 3}
                    else:
                        token["expires_in"] = 3

        except asyncio.CancelledError:
            pass

        logger.info("Stopping token auto-renew task")

    def _auto_renew_task_done_cb(self, task, *args, **kwargs):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception("Renew task exception detected!")

    def stop_refreshing(self):
        logger.debug('Stop refreshing Oauth2 token...')
        if self._renew_task is not None:
            self._renew_task.cancel()
            self._renew_task = None


# class AsyncPyJWKClient(jwt.PyJWKClient):  # TODO think about it... a background task that refreshes keys could be a good solution


class JWTTokenValidator:

    def __init__(
            self, oidc_config_url: str, skip_ssl=False,
            required_claims: list[str] | None = None,
            required_audience: list[str] | str | None = None
    ):
        self._oidc_config_url = oidc_config_url
        self._skip_ssl = skip_ssl
        self._jwks_client: jwt.PyJWKClient | None = None
        self._oidc_signing_algorithms: list | None = None

        self._required_claims: list[str] = required_claims or []
        self._required_audience: list[str] | str | None = required_audience
        # TODO add required scopes/roles?

    async def _maybe_load_jwkset(self):
        if self._jwks_client is None:
            logger.info(f'Loading JWKSet from {self._oidc_config_url}')
            async with aiohttp.ClientSession() as session:
                async with session.get(self._oidc_config_url, ssl=not self._skip_ssl) as r:
                    oidc_config = await r.json()

            ssl_context = None
            if self._skip_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            self._oidc_signing_algorithms = oidc_config["id_token_signing_alg_values_supported"]
            self._jwks_client = jwt.PyJWKClient(uri=oidc_config["jwks_uri"], ssl_context=ssl_context)

    async def validate(
            self,
            access_token: str,
            print_exception_on_invalid_tokens=False
    ) -> dict | None:
        try:
            await self._maybe_load_jwkset()
        except Exception:
            logger.exception(f'Cannot load JWKSet from {self._oidc_config_url}!')
            return None

        try:
            res = await asyncio.to_thread(  # Uses urllib internally...
                jwt.decode,
                jwt=access_token,
                key=self._jwks_client.get_signing_key_from_jwt(access_token).key,
                algorithms=self._oidc_signing_algorithms,
                options={
                    'require': self._required_claims,
                    'verify_iat': False,
                    'verify_aud': self._required_audience is not None
                },
                audience=self._required_audience
            )
            logger.debug('Got a valid JWT')
            return res
        except jwt.PyJWTError:
            if print_exception_on_invalid_tokens:
                logger.exception(f'Got invalid JWT! {access_token}')
            else:
                logger.error(f'Got invalid JWT! {access_token}')
            return None

#
# def is_token_expired(token: str) -> bool:
#     header = jwt.get_unverified_header(token)
#     decoded_token = jwt.decode(token, algorithms=header['alg'])