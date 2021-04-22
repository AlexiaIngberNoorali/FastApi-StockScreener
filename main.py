# pip3 install -r requirements.txt
# uvicorn main:app --reload

from typing import Optional
import db_models
import yfinance as yf
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db_models import Stock

app = FastAPI()
# Create the db (see database.py)
db_models.Base.metadata.create_all(bind=engine)


def get_db():
    """
    Ensure that a session can open properly if not it closes
    :return: content of db session
    """
    try:
        db = SessionLocal()
        # read as return (which not used so we are not exiting the function)
        yield db
    # <finally> executed wheter the try is executed or not (opposite to except)
    finally:
        db.close()


# Find directory where to look for templates (Templates)
templates = Jinja2Templates(directory="templates")


# Defining Model
class StockRequest(BaseModel):
    symbol: str


# Defining Routes/Controllers
@app.get("/")
def home(request: Request, forward_pe=None, dividend_yield=None, ma50=None, ma200=None, db: Session = Depends(get_db)):
    """
    displays the stock screener home.html / homepage

    """
    stocks = db.query(Stock)

    # Filters
    if forward_pe:
        stocks = stocks.filter(Stock.forward_pe < forward_pe)

    if dividend_yield:
        stocks = stocks.filter(Stock.dividend_yield > dividend_yield)

    if ma50:
        stocks = stocks.filter(Stock.price > Stock.ma50)

    if ma200:
        stocks = stocks.filter(Stock.price > Stock.ma200)

    return templates.TemplateResponse("home.html", {
        "request": request,
        "stocks": stocks,
        "dividend_yield": dividend_yield,
        "forward_pe": forward_pe,
        "ma200": ma200,
        "ma50": ma50
    })


def fetch_stock_data(id: int):
    """
    Fetch data from yahoo finance
    :param id: Id corresponding to the symbol entered
    :return: data_info from yahoo finance
    """
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.id == id).first()

    yahoo_data = yf.Ticker(stock.symbol)

    stock.ma200 = yahoo_data.info['twoHundredDayAverage']
    stock.ma50 = yahoo_data.info['fiftyDayAverage']
    stock.price = yahoo_data.info['previousClose']
    stock.forward_pe = yahoo_data.info['forwardPE']
    stock.forward_eps = yahoo_data.info['forwardEps']
    if yahoo_data.info['dividendYield']:
        stock.dividend_yield = yahoo_data.info['dividendYield'] * 100

    db.add(stock)
    db.commit()


# We want the get_db function to be executed before using the db parameter in the current function
@app.post("/stock/")
async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    created a stock and stores it in the database

    """
    stock = Stock()
    stock.symbol = stock_request.symbol

    db.add(stock)
    db.commit()

    background_tasks.add_task(fetch_stock_data, stock.id)

    return {"code": "success",
            "message": "stock created"
            }
