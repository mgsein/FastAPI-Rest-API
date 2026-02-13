from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import asyncio
from time import sleep
from datetime import datetime, UTC
from os import environ
from http import HTTPStatus
import logs, db, logging
from typing import Annotated
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO



app = FastAPI()
app.mount('/static', StaticFiles(directory='static'))

MAX_IMAGE_SIZE = 5 * 1024 * 1024 # 5MB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-5dT%H:%M:%S',
)

@app.post('/survey')
def survey(
    name: Annotated[str, Form()],
    happy: Annotated[str, Form()],
    talk: Annotated[str, Form()],
):
    logging.info('[survey] name: %r, happy: %r, talk: %r', name, happy, talk)
    return RedirectResponse(
        url='/static/thanks.html',
        status_code=HTTPStatus.FOUND,
    )

app.post('/size')
async def size(request: Request):
    size = int(request.headers.get('Content-Length', 0))
    if not size:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='missing content-length header',
        )
    if size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='image too large (max is 5MB)',
        )

    data = await request.body()
    io = BytesIO(data)
    img = Image.open(io)
    return {'width': img.width, 'height': img.height}

class Sale(BaseModel):
    time: datetime
    customer_id: str = Field(min_length=2)
    sku: str = Field(min_length=2)
    amount: int = Field(gt=0)
    price: float = Field(gt=0) #$

@app.post('/sales/')
def new_sale(sale: Sale):
    record = db.Sale(
        time=sale.time,
        sku=sale.sku,
        customer_id=sale.customer_id,
        amount=sale.amount,
        price=int(sale.price * 100),
    )
    key = db.insert(record)
    return {
        'key': key,
    }

@app.get('/sales/{key}')
def get_salary(key: str) -> Sale:
    record = db.get(key)
    if record is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='sale not found')
    
    s = Sale(
        time=record.time,
        sku=record.sku,
        customer_id=record.customer_id,
        amount=record.amount,
        price=record.price / 100,
    )
    return s

@app.get('/logs')
def logs_query(start: datetime, end: datetime, level: str = None):
    if start >= end:
        raise HTTPException (
            status_code=HTTPStatus.BAD_REQUEST, detail='start must before end'
        )
    if not level or not logs.is_valid_level(level):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='invalid log level'
        )
    
    records = logs.query(start, end, level)
    if not records:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='no lgos found')
    
    return {
        'count': len(records),
        'records': records,
    }

@app.get('/sleep/sys')
def nsys_sleep():
    sleep(1)
    return {'error': None}

@app.get('/sleep/async-sys')
async def sys_sleep():
    sleep(1)
    return {'error': None}

@app.get('/sleep/async-aio')
async def aio_sleep():
    await asyncio.sleep(1)
    return {'error': None}

@app.get('/health')
def health():
    return {'errors': None}

@app.get('/info')
def info():
    return {
        'version': '0.1.0',
        'time': datetime.now(tz=UTC),
        'user': environ['USER'],
    }

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)