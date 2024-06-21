"""Catalogue map for ABS data."""

import pandas as pd
from io import StringIO

def catalogue_map() -> pd.DataFrame:
    """Return the catalogue map."""

    csv = """Catalogue ID,Theme,Parent Topic,Topic,URL,Status
1364.0.15.003,Economy,National Accounts,Modellers Database,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
3101.0,People,Population,National State And Territory Population,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
3222.0,People,Population,Population Projections Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
3401.0,Industry,Tourism And Transport,Overseas Arrivals And Departures Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5204.0,Economy,National Accounts,Australian System National Accounts,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5206.0,Economy,National Accounts,Australian National Accounts National Income Expenditure And Product,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5220.0,Economy,National Accounts,Australian National Accounts State Accounts,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5232.0,Economy,National Accounts,Australian National Accounts Finance And Wealth,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5232.0.55.001,Economy,Finance,Assets And Liabilities Australian Securitisers,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5302.0,Economy,International Trade,Balance Payments And International Investment Position Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5368.0,Economy,International Trade,International Trade Goods And Services Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5368.0.55.024,Economy,International Trade,International Merchandise Trade Preliminary Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5601.0,Economy,Finance,Lending Indicators,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5625.0,Economy,Business Indicators,Private New Capital Expenditure And Expected Expenditure Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5655.0,Economy,Finance,Managed Funds Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5676.0,Economy,Business Indicators,Business Indicators Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5681.0,Economy,Business Indicators,Monthly Business Turnover Indicator,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
5682.0,Economy,Finance,Monthly Household Spending Indicator,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6202.0,Labour,Employment And Unemployment,Labour Force Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6150.0.55.003,Labour,Labour Accounts,Labour Account Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6248.0.55.002,Labour,Employment And Unemployment,Public Sector Employment And Earnings,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6291.0.55.001,Labour,Employment And Unemployment,Labour Force Australia Detailed,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6302.0,Labour,Earnings And Working Conditions,Average Weekly Earnings Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6321.0.55.001,Labour,Earnings And Working Conditions,Industrial Disputes Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6345.0,Economy,Price Indexes And Inflation,Wage Price Index Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6354.0,Labour,Jobs,Job Vacancies Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6401.0,Economy,Price Indexes And Inflation,Consumer Price Index Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6416.0,Economy,Price Indexes And Inflation,Residential Property Price Indexes Eight Capital Cities,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory,Ceased
6427.0,Economy,Price Indexes And Inflation,Producer Price Indexes Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6432.0,Economy,Price Indexes And Inflation,Total Value Dwellings,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6457.0,Economy,Price Indexes And Inflation,International Trade Price Indexes Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6467.0,Economy,Price Indexes And Inflation,Selected Living Cost Indexes Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
6484.0,Economy,Price Indexes And Inflation,Monthly Consumer Price Index Indicator,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
7215.0,Industry,Agriculture,Livestock Products Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
7218.0.55.001,Industry,Agriculture,Livestock And Meat Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory,Ceased
8155.0,Industry,Industry Overview,Australian Industry,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8165.0,Economy,Business Indicators,Counts Australian Businesses Including Entries And Exits,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8412.0,Industry,Mining,Mineral And Petroleum Exploration Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8501.0,Industry,Retail And Wholesale Trade,Retail Trade Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8701.0,Industry,Building And Construction,Estimated Dwelling Stock,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8731.0,Industry,Building And Construction,Building Approvals Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8752.0,Industry,Building And Construction,Building Activity Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8755.0,Industry,Building And Construction,Construction Work Done Australia Preliminary,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8762.0,Industry,Building And Construction,Engineering Construction Activity Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory, 
8782.0.65.001,Industry,Building And Construction,Construction Activity Chain Volume Measures Australia,https://www.abs.gov.au/about/data-services/help/abs-time-series-directory,Ceased
"""
    return pd.read_csv(StringIO(csv), index_col=0)

