from fastapi import FastAPI
import asyncio
from time import sleep
from datetime import datetime, UTC
from os import environ

app = FastAPI()

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