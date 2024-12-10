import logging
from json import JSONDecodeError

import httpx
from databases import Database

from storeapi.config import config
from storeapi.database import post_table

logger = logging.getLogger(__name__)

MAILGUN_API_URL: str = "https://api.mailgun.net/v3/"
CUTE_CREATURE_GENERATOR_URL: str = "https://api.deepai.org/api/cute-creature-generator"


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


async def _generate_cute_creature_api(prompt: str):
    logger.debug("Generating cute creature with prompt: {}".format(prompt[:20]))
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                CUTE_CREATURE_GENERATOR_URL,
                data={"text": prompt},
                headers={"api-key": config.DEEPAPI_API_KEY or ""},
                timeout=60,
            )
            logger.debug(response)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                "API request failed with status code {}".format(
                    err.response.status_code
                )
            ) from err
        except (JSONDecodeError, TypeError) as err:
            raise APIResponseError("API response parsing failed") from err


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = "A cute cat sitting on a chair.",
):
    try:
        response = await _generate_cute_creature_api(prompt)
    except APIResponseError:
        return await send_simple_email(
            email,
            "Error generating image",
            (
                f"Hi {email},\n\nUnfurtonately, there was an error generating the image for your post."
            ),
        )
    logger.debug("Connection to the database to update post")

    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=response["output_url"])
    )

    logger.debug(query)
    await database.execute(query)

    logger.debug("Completed updating post")

    await send_simple_email(
        email,
        "Successfully added image to your post",
        (
            f"Hi {email},\n\n"
            "You have successfully added an image to your post. Please click the link below to view your post.\n"
            f"{post_url}\n\n"
        ),
    )

    return response
