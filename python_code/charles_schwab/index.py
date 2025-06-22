# pip install requests loguru

# 2025-06-21 17:50:40.933 | DEBUG    | __main__:main:74 - {'expires_in': 1800, 'token_type': 'Bearer', 'scope': 'api', 
# 'refresh_token': 'GjnbLebsOZl3y4RnSAKMqtieCmSmKtTmJd__tL6sln0jH_-E1Jj7iluRu0vlP_TwbD5MyTriDdEg77_5460aXJoPj82jth8HAsu9Zz8-HQTSZ4CpffBKersv3Hh2beZS52wB2811YgQ@', 
# 'access_token': 'I0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.Lt0aCttlnNJQ_EKkSKvttOa6f7La2f1PDbFKFpAF_s8@', 
# 'id_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0NWViMGRjMjBjMjViODQ3ZGViZGI1MDFkMTBmYTBkZTlmYWMwYTIyOGVlYzg0MTJmMzVkZDhmM2RhYmY1ZmFkIiwiYXVkIjoiYkFuV3FtN0lmVWM3MVpBZ1BOM1lCRWN2WGMxQ2c2QXoiLCJpc3MiOiJ1cm46Ly9hcGkuc2Nod2FiYXBpLmNvbSIsImV4cCI6MTc1MDU1MzQ0MCwiaWF0IjoxNzUwNTQ5ODQwLCJqdGkiOiIyMDg3Mjg0Ni1hNDNlLTQ1NzAtODNkMy00MjZhNDZlYTU4MmMifQ.5tDYo-6RIq81AHTMJbf8dLGmDf9ug-3-l4emkOlRjbM'}

import os
import base64
import requests
import webbrowser
from loguru import logger

def construct_init_auth_url() -> tuple[str, str, str]:

    app_key = "bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az"
    app_secret = "80gy0PgRJAUqPOMA"

    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri=https://127.0.0.1"

    logger.info("Click to authenticate:")
    logger.info(auth_url)

    return app_key, app_secret, auth_url


def construct_headers_and_payload(returned_url, app_key, app_secret):
    response_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

    credentials = f"{app_key}:{app_secret}"
    base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
        "utf-8"
    )

    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "grant_type": "authorization_code",
        "code": response_code,
        "redirect_uri": "https://127.0.0.1",
    }

    return headers, payload


def retrieve_tokens(headers, payload) -> dict:
    init_token_response = requests.post(
        url="https://api.schwabapi.com/v1/oauth/token",
        headers=headers,
        data=payload,
    )

    init_tokens_dict = init_token_response.json()

    return init_tokens_dict


def main():
    app_key, app_secret, cs_auth_url = construct_init_auth_url()
    webbrowser.open(cs_auth_url)

    logger.info("Paste Returned URL:")
    returned_url = input()

    init_token_headers, init_token_payload = construct_headers_and_payload(
        returned_url, app_key, app_secret
    )

    init_tokens_dict = retrieve_tokens(
        headers=init_token_headers, payload=init_token_payload
    )

    logger.debug(init_tokens_dict)

    return "Done!"


if __name__ == "__main__":
    main()