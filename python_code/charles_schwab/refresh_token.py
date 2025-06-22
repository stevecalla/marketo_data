import os
from flask import Request
import base64
import requests
from loguru import logger


def refresh_tokens():
    logger.info("Initializing...")

    app_key = "bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az"
    app_secret = "80gy0PgRJAUqPOMA"

    # You can pull this from a local file,
    # Google Cloud Firestore/Secret Manager, etc.
    # refresh_token_value = "your-current-refresh-token"
    refresh_token_value = "GjnbLebsOZl3y4RnSAKMqtieCmSmKtTmJd__tL6sln0jH_-E1Jj7iluRu0vlP_TwbD5MyTriDdEg77_5460aXJoPj82jth8HAsu9Zz8-HQTSZ4CpffBKersv3Hh2beZS52wB2811YgQ@"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
    }
    headers = {
        "Authorization": f'Basic {base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()}',
        "Content-Type": "application/x-www-form-urlencoded",
    }

    refresh_token_response = requests.post(
        url="https://api.schwabapi.com/v1/oauth/token",
        headers=headers,
        data=payload,
    )
    if refresh_token_response.status_code == 200:
        logger.info("Retrieved new tokens successfully using refresh token.")
    else:
        logger.error(
            f"Error refreshing access token: {refresh_token_response.text}"
        )
        return None

    refresh_token_dict = refresh_token_response.json()

    logger.debug(refresh_token_dict)

    logger.info("Token dict refreshed.")

    return "Done!"

if __name__ == "__main__":
  refresh_tokens()