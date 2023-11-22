from datetime import datetime
from enum import Enum
from pandas import DataFrame, read_csv
from logging import basicConfig, getLogger, INFO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Configure logging
basicConfig(level=INFO)
logger = getLogger(__name__)

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

@app.get("/peaks")
async def get_top5_peaks_for_market(market_name: str) -> List[EnergyUsage]:
    """This endpoint returns the 5 highest energy usage periods for a market."""
    try:
        if market_name not in EnergyMarket.__members__:
            raise ValueError("Invalid market name")

        markets_df = read_csv('markets.csv')
        usage_df = read_csv('usage.csv')

        for ts in usage_df['timestamp']:
            try:
                datetime.fromisoformat(ts)
            except ValueError:
                logger.error(f"Invalid timestamp format: {ts}", exc_info=True)
                raise ValueError(f"Invalid timestamp format: {ts}")

        merged_data = DataFrame.merge(usage_df, markets_df, left_on='market_id', right_on='id')
        filtered_data = merged_data[merged_data['name'] == market_name]

        if filtered_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for market: {market_name}")

        sorted_data = filtered_data.sort_values(by='usage_kw', ascending=False)
        top5_records = sorted_data.head(5)

        result: List[EnergyUsage] = []
        for _, row in top5_records.iterrows():
            energy_usage = EnergyUsage(
                usage_kw=row['usage_kw'],
                market_name=EnergyMarket(row['name']),
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
            result.append(energy_usage)

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
