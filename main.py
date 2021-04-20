# pip3 install -r requirements.txt
# uvicorn main:app --reload

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    """
    displays the stock screener home.html / homepage

    """
    return templates.TemplateResponse("home.html", {
        "request": request,
        "somevar": 2
    })


@app.post("/stock")
def create_stock():
    """
    created a stock and stores it in the database

    """
    return {"code": "success",
            "message": "stock created"
            }
