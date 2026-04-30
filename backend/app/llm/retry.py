import asyncio
import httpx

from app.llm.exceptions import LLMHTTPError, LLMRateLimitError, LLMTimeoutError


async def post_with_retry(client, url, headers, json, retries=3):
    last_429: httpx.HTTPStatusError | None = None
    for i in range(retries):
        try:
            resp = await client.post(url, headers=headers, json=json)
            resp.raise_for_status()
            return resp

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # 限流
                last_429 = e
                if i == retries - 1:
                    break
                await asyncio.sleep(0.5 * (2 ** i))
            else:
                raise LLMHTTPError(str(e))

        except httpx.TimeoutException as e:
            if i == retries - 1:
                raise LLMTimeoutError(str(e)) from e
            await asyncio.sleep(0.5 * (2 ** i))
        except Exception:
            if i == retries - 1:
                raise
            await asyncio.sleep(0.5 * (2 ** i))

    if last_429 is not None:
        raise LLMRateLimitError("LLM 请求触发限流，请稍后重试") from last_429
    raise LLMHTTPError("LLM 请求失败")
