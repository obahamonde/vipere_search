from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from pydantic import HttpUrl
from typing import List, Dict, Any, Union, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

AGENT = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)AppleWebKit/605.1.15 (KHTML, like Gecko)Version/12.1.1 Safari/605.1.15"""

default_headers = {
    "User-Agent": AGENT
}

async def fetch(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Union[str, bytes, Dict[str, Any]]:
    """
    Asynchronously send an HTTP request and return the response content as text, bytes, or JSON.

    Args:
        url (str): The URL to send the request to.
        method (str, optional): The HTTP method to use for the request. Defaults to "GET".
        headers (Optional[Dict[str, str]], optional): An optional dictionary of headers to include in the request. Defaults to None.
        body (Optional[bytes], optional): An optional bytes-like object to include as the request body. Defaults to None.
        json (Optional[Dict[str, Any]], optional): An optional dictionary to send as JSON in the request body. Defaults to None.

    Returns:
        Union[str, bytes, Dict[str, Any]]: The response content as a string, bytes, or a dictionary (in case of JSON response).

    Raises:
        ValueError: If both `body` and `json` parameters are provided.
    """
    if body is not None and json is not None:
        raise ValueError("Both `body` and `json` parameters cannot be provided.")

    async with ClientSession() as session:
        async with session.request(
            method=method, url=url, headers=headers, data=body, json=json
        ) as response:
            content_type = response.content_type

            if content_type.endswith("json"):
                return await response.json()
            if content_type.startswith("text/"):
                return await response.text()

            return await response.read()

async def scrape(url:str, el:dict):
    response = await fetch(url, headers= {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"})
    if isinstance(response, str):
        soup = BeautifulSoup(response, "lxml")
        for k,v in el.items():
            if k == "_class":
                item = soup.find_all(el["tag"], class_=v)
            else:
                item = soup.find_all(el["tag"], id=v)
            yield item

static = StaticFiles(directory="dist", html=True)

   
    
app = FastAPI()

@app.get("/api/{lang}/{query}/{page}")
async def main(lang:str, query:str, page:int):
    url=f"https://www.google.com/search?q={query}&lr=lang_{lang}&start={str(page*10)}"
    headers = default_headers
    el = {"tag":"div", "_class":"yuRUbf"}
    items = []
    async for item in scrape(url, el):
        for i in item:
            items.append({"title":i.find("h3").text, "url":i.find("a")["href"]})
    return items

app.mount("/", static, name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)