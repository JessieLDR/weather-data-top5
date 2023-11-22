from datetime import datetime
from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()


class EnergyMarket(str, Enum):
    caiso = "caiso"
    spp = "spp"
    ercot = "ercot"
    ieso = "ieso"
    aeso = "aeso"
    nyiso = "nyiso"
    pjm = "pjm"
    miso = "miso"
    isone = "isone"


class EnergyUsage(BaseModel):
    usage_kw: float
    market_name: EnergyMarket
    timestamp: datetime


@app.get("/")
def default_route():
    return {"slogan": "Better Energy, More Cash."}


@app.on_event("startup")
def on_startup():
    pass


@app.get("/peaks")
async def get_top5_peaks_for_market(market_name: str) -> List[EnergyUsage]:
    """This endpoint returns the 5 highest energy usage periods for a market."""
    # task:  complete this function and return correct, and correctly typed values.
    result: List[EnergyUsage] = []
    return result
