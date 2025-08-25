import asyncio
import os
from typing import Optional

from ..main import extract_ultimate_pure_data


async def _run_demo() -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found")
        return
    result = await extract_ultimate_pure_data(
        query_text="renewable energy capacity statistics worldwide",
        search_depth="basic",
        max_sources=3,
        groq_api_key=api_key,
    )
    print("Points:", len(result.get("raw_data_points", [])))


def main() -> None:
    asyncio.run(_run_demo())


if __name__ == "__main__":
    main()

