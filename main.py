from fastapi import FastAPI, HTTPException
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup
from cachetools import TTLCache

app = FastAPI()

cache = TTLCache(maxsize=100, ttl=300)

async def fetch_meta_data(url: str):
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    if url in cache:
        return cache[url]

    try:
        connector = TCPConnector(ssl=False, limit=50, keepalive_timeout=10)

        async with ClientSession(connector=connector) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch URL")

                html = await response.text()
                head_start = html.find("<head>")
                head_end = html.find("</head>") + len("</head>")
                head_content = html[head_start:head_end]

                soup = BeautifulSoup(head_content, "html.parser")

                title = soup.title.string if soup.title else ""
                description = soup.find("meta", attrs={"name": "description"})
                description = description["content"] if description else ""
                og_title = soup.find("meta", property="og:title")
                og_title = og_title["content"] if og_title and og_title.has_attr("content") else ""
                og_description = soup.find("meta", property="og:description")
                og_description = og_description["content"] if og_description and og_description.has_attr("content") else ""
                og_image = soup.find("meta", property="og:image")
                og_image = og_image["content"] if og_image and og_image.has_attr("content") else ""

                meta_data = {
                    "title": og_title or title,
                    "description": og_description or description,
                    "image": og_image,
                }
                cache[url] = meta_data
                return meta_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {e}")

@app.get("/meta")
async def get_meta_data(url: str):
    return await fetch_meta_data(url)