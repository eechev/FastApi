import logging

import httpx

from storeapi.config import config

logger = logging.getLogger(__name__)

MAILGUN_API_URL: str = "https://api.mailgun.net/v3/"


class APIResponseError(Exception):
    pass


async def send_simple_email(email: str, subject: str, body: str):
    logger.debug("Sending email to {}".format(email[:3]))
    logger.debug("Subject: {}".format(subject[:20]))
    logger.debug("Body: {}".format(body[:20]))

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                MAILGUN_API_URL + (config.MAILGUN_DOMAIN or "") + "/messages",
                auth=("api", config.MAILGUN_API_KEY or ""),
                data={
                    "from": "Store API <mailgun@" + (config.MAILGUN_DOMAIN or "") + ">",
                    "to": [email],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug(response.content)
            return response
        except httpx.HTTPStatusError as e:
            logger.error("API request failed: {}".format(e))
            raise APIResponseError(
                f"API request failed with status code {e.response.status_code}"
            ) from e


async def send_user_registration_email(email: str, confirmation_url: str):
    return await send_simple_email(
        email,
        "Successfully registered to Store API",
        (
            f"Hi {email},\n\n"
            "You have successfully registered to Store API. Please click the link below to confirm your email.\n"
            f"{confirmation_url}\n\n"
        ),
    )
