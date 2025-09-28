import random
import string
import os
import json
import http
from fastapi import HTTPException
import httpx
import redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from redis.exceptions import ConnectionError, TimeoutError, RedisError
from urllib.parse import urlparse
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USERNAME = os.getenv("REDIS_USERNAME", None)
logger = logging.getLogger("uvicorn")

class RedisManager:
    def __init__(self, **kwargs):
        self.redis_config = kwargs
        self.client = None

    async def connect(self):
        retries = 5
        delay = 1

        for attempt in range(1, retries + 1):
            try:
                logger.info("Connecting to Redis Cluster...")
                self.client = Redis(**self.redis_config)
                # Test the connection
                await self.client.ping()
                logger.info("Connected to Redis Cluster.")
                return
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Redis connection attempt {attempt} failed: {e}")
                await asyncio.sleep(delay)
                delay *= 2  # exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error during Redis connection: {e}")
                break

        logger.error("Failed to connect to Redis after retries.")
        raise RuntimeError("Could not connect to Redis.")

    async def reconnect(self):
        logger.info("Attempting Redis reconnect...")
        await self.aclose()
        await self.connect()

    async def aclose(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def safe_execute(self, command, *args, **kwargs):
        try:
            method = getattr(self.client, command)
            return await method(*args, **kwargs)
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"Redis command '{command}' failed: {e}")
            await self.reconnect()
            method = getattr(self.client, command)
            return await method(*args, **kwargs)

redis_manager = RedisManager(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    username=REDIS_USERNAME,
    password=REDIS_PASSWORD,
)

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def format_user_principal_name(user_principal_name: str) -> str:
    if '#EXT#' in user_principal_name:
        username_part, _ = user_principal_name.split('#EXT#')
        formatted_email=username_part.replace('_outlook.com', '@outlook.com')
        return formatted_email
    return user_principal_name


def create_error_html(error_message,base_url):
    if "localhost" in base_url or "127.0.0.1" in base_url:
        target_origin = "http://localhost:3000"
    else:
        target_origin = base_url.rstrip("/") 
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Error</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 40px; }}
            .error-container {{ max-width: 500px; margin: 0 auto; background-color: #fff3f3; border: 1px solid #ffcaca; padding: 20px; border-radius: 5px; }}
            h3 {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h3>Authentication Failed</h3>
            <p>{error_message}</p>
        </div>
        <script>
            try {{
                const message = {{ type: 'auth_error', error: "{error_message}" }};
                const targetOrigin = '{target_origin}';
                if (window.opener) {{
                    window.opener.postMessage(message, targetOrigin);
                }}
            }} catch (e) {{
                console.error("Error sending message to opener:", e);
            }}
        </script>
    </body>
    </html>
    """


def create_success_html(access_token,base_url):
    if "localhost" in base_url or "127.0.0.1" in base_url:
        target_origin = "http://localhost:3000"
    else:
        target_origin = base_url.rstrip("/") 
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authenticating...</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 40px; }}
            .success-container {{ max-width: 500px; margin: 0 auto; background-color: #f0fff0; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; }}
            h3 {{ color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="success-container">
            <h3>Authentication Successful</h3>
            <p>You have been successfully authenticated. This window will close automatically.</p>
        </div>
        <script>
            try {{
                const token = "{access_token}";
                const message = {{ type: 'auth_success', token: token }};
                const targetOrigin = '{target_origin}';
                if (window.opener) {{
                    window.opener.postMessage(message, targetOrigin);
                }} else {{
                    console.error("No window.opener found");
                }}
            }} catch (e) {{
                console.error("Error sending message to opener:", e);
                if (window.opener) {{
                    window.opener.postMessage({{ type: 'auth_error', error: 'Failed to send token' }}, window.opener.location.origin);
                }}
            }}
        </script>
    </body>
    </html>
    """


# async def notify_slack_error(user_id: str, error_message: str):
#     payload = {
#         "text": f"Error from {user_id}\n```{error_message}```"
#     }
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(SLACK_WEBHOOK_URL, json=payload)
#             print(response.text)
#     except Exception as slack_error:
#         print(f"Slack notification failed: {slack_error}")


async def check_stop_conversation(session_id: str, message_id: str):
    stop_msg = await redis_manager.safe_execute("get", f"stop:{session_id}")
    if stop_msg == message_id:
        return True
    else:
        return False