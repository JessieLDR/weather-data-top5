from datetime import datetime
from enum import Enum
from pandas import DataFrame, read_csv, to_datetime
from heapq import nlargest
from logging import basicConfig, getLogger, INFO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Configure logging
basicConfig(level=INFO)
logger = getLogger(__name__)

class EnergyMarket(str, Enum):
    CAISO = "caiso"
    SPP = "spp"
    ERCOT = "ercot"
    IESO = "ieso"
    AESO = "aeso"
    NYISO = "nyiso"
    PJM = "pjm"
    MISO = "miso"
    ISONE = "isone"

class EnergyUsage(BaseModel):
    usage_kw: float
    market_name: EnergyMarket
    timestamp: datetime

@app.get("/")
def default_route():
    return {"slogan": "Better Energy, More Cash."}

@app.get("/peaks")
async def get_top5_peaks_for_market(market_name: str) -> List[EnergyUsage]:
    try:
        # Convert market_name to lowercase for case-insensitive comparison
        if market_name.lower() not in (market.value for market in EnergyMarket):
            raise ValueError("Invalid market name")

        markets_df = read_csv('markets.csv')
        usage_df = read_csv('usage.csv')

        usage_df['timestamp'] = to_datetime(usage_df['timestamp'])
        usage_df['date'] = usage_df['timestamp'].dt.date

        merged_data = DataFrame.merge(usage_df, markets_df, left_on='market_id', right_on='id')
        filtered_data = merged_data[merged_data['name'].str.lower() == market_name.lower()]

        if filtered_data.empty:
            raise HTTPException(status_code=404, detail="No data found for market: {market_name}")

        peak_queue = [(row['usage_kw'], row['timestamp'], row['name']) for _, row in filtered_data.iterrows()]
        top5_peaks = nlargest(5, peak_queue, key=lambda x: x[0])

        result = [
            EnergyUsage(
                usage_kw=peak[0],
                market_name=EnergyMarket(peak[2]),
                timestamp=peak[1]
            ) 
            for peak in top5_peaks
        ]

        return result

    except ValueError as e:
        logger.error(f"Value error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
