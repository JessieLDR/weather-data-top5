from datetime import datetime
from enum import Enum
from pandas import DataFrame, read_csv, to_datetime
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
    try:
        if market_name not in EnergyMarket.__members__:
            raise ValueError("Invalid market name")

        markets_df = read_csv('markets.csv')
        usage_df = read_csv('usage.csv')

        # Convert 'timestamp' string to datetime object and extract the date
        usage_df['timestamp'] = to_datetime(usage_df['timestamp'])
        usage_df['date'] = usage_df['timestamp'].dt.date

        merged_data = DataFrame.merge(usage_df, markets_df, left_on='market_id', right_on='id')
        filtered_data = merged_data[merged_data['name'] == market_name]

        if filtered_data.empty:
            raise HTTPException(status_code=404, detail="No data found for market: {market_name}")

        # Group by date, find max usage each day
        daily_max = filtered_data.groupby('date')['usage_kw'].max().reset_index()

        # Merge back to get the full row for each peak
        top_daily_peaks = daily_max.merge(filtered_data, on=['date', 'usage_kw'])

        # Sort by usage and select the top 5 peaks
        top5_peaks = top_daily_peaks.sort_values(by='usage_kw', ascending=False).head(5)

        result: List[EnergyUsage] = []
        for _, row in top5_peaks.iterrows():
            energy_usage = EnergyUsage(
                usage_kw=row['usage_kw'],
                market_name=EnergyMarket(row['name']),
                timestamp=row['timestamp']  # Keeping the full timestamp here
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