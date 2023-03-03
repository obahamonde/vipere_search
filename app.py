from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from mangum import Mangum
from pydantic import HttpUrl
from typing import List, Dict, Any, Union
from fastapi.middleware.cors import CORSMiddleware

AGENT = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)AppleWebKit/605.1.15 (KHTML, like Gecko)Version/12.1.1 Safari/605.1.15"""

default_headers = {
    "User-Agent": AGENT
}

class SearchMicroservice(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    async def fetch(self, url: Union[str, HttpUrl]) -> Union[Dict[str, Any], str, bytes]:
        try:
            async with ClientSession() as session:
                async with session.get(url=url,headers={"user-agent": AGENT}) as response:
                        return await response.json()
        except Exception as execption:
            raise HTTPException(status_code=500, detail=str(execption))
    
    async def fetch_html(self, url: Union[HttpUrl,str],headers: Dict[str, Any]) -> str:
        """Used to fetch HTML"""
        async with ClientSession() as session:
            async with session.get(url, headers={"user-agent": AGENT}) as response:
                return await response.text(encoding='utf-8')
            
    async def parse(self, html:str)->BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        return soup
    
    async def search(self,lang:str, query:str, page:int)->List[Dict[str,Any]]:
        try:
            response = await self.fetch_html(url=f"https://www.google.com/search?q={query}&lr=lang_{lang}&start={str(page*10)}", headers={"user-agent": AGENT})
            urls = [link.find("a")["href"] for link in BeautifulSoup(response, "lxml").find_all("div", class_="yuRUbf")]
            summaries = [link.find("h3").text for link in BeautifulSoup(response, "lxml").find_all("div", class_="yuRUbf")]   
            return [{"url":item[0],"title":item[1]} for item in list(zip(urls, summaries))]
        except Exception as execption:
            raise HTTPException(status_code=500, detail=str(execption))
    
app = SearchMicroservice()

@app.get("/api/{lang}/{query}/{page}")
async def main(lang:str, query:str, page:int):
    return await app.search(lang, query, page)

@app.get("/")
async def root():
    return {
        "service": "Search Microservice",
        "version": "1.0.0",
        "methods": ["GET"],
        "payload_example":{
            "lang":"en",
            "query":"fastapi",
            "page":0
        },
        "author": "Oscar Bahamonde",
        "github": "obahamonde",
        "email": "ob@obahamonde.com"
    }
        
handler = Mangum(app)