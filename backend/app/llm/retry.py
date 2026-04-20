import asyncio
import httpx

from app.llm.exceptions import LLMHTTPError


async def post_with_retry(client, url, headers, json, retries=3):
    for i in range(retries):
        try:
            resp = await client.post(url, headers=headers, json=json)
            resp.raise_for_status()
            return resp

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # 限流
                await asyncio.sleep(0.5 * (2 ** i))
            else:
                raise LLMHTTPError(str(e))

        except Exception:
            if i == retries - 1:
                raise
            await asyncio.sleep(0.5 * (2 ** i))
