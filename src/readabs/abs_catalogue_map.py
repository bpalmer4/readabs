"""Catalogue map for ABS data."""

from io import StringIO

from pandas import DataFrame, read_csv


def catalogue_map() -> DataFrame:
    """Return the catalogue map."""

    csv = """Catalogue ID,Theme,Parent Topic,Topic,URL,Status
1364.0.15.003,Economy,National Accounts,Modellers Database,https://www.abs.gov.au/statistics/economy/national-accounts/modellers-database/latest-release, 
3101.0,People,Population,National State And Territory Population,https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release, 
3222.0,People,Population,Population Projections Australia,https://www.abs.gov.au/statistics/people/population/population-projections-australia/latest-release, 
3401.0,Industry,Tourism And Transport,Overseas Arrivals And Departures Australia,https://www.abs.gov.au/statistics/industry/tourism-and-transport/overseas-arrivals-and-departures-australia/latest-release, 
5204.0,Economy,National Accounts,Australian System National Accounts,https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release, 
5206.0,Economy,National Accounts,Australian National Accounts National Income Expenditure And Product,https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-national-income-expenditure-and-product/latest-release, 
5220.0,Economy,National Accounts,Australian National Accounts State Accounts,https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/latest-release, 
5232.0,Economy,National Accounts,Australian National Accounts Finance And Wealth,https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-finance-and-wealth/latest-release, 
5232.0.55.001,Economy,Finance,Assets And Liabilities Australian Securitisers,https://www.abs.gov.au/statistics/economy/finance/assets-and-liabilities-australian-securitisers/latest-release, 
5302.0,Economy,International Trade,Balance Payments And International Investment Position Australia,https://www.abs.gov.au/statistics/economy/international-trade/balance-payments-and-international-investment-position-australia/latest-release, 
5368.0,Economy,International Trade,International Trade Goods And Services Australia,https://www.abs.gov.au/statistics/economy/international-trade/international-trade-goods-and-services-australia/latest-release, 
5368.0.55.024,Economy,International Trade,International Merchandise Trade Preliminary Australia,https://www.abs.gov.au/statistics/economy/international-trade/international-merchandise-trade-preliminary-australia/latest-release, 
5601.0,Economy,Finance,Lending Indicators,https://www.abs.gov.au/statistics/economy/finance/lending-indicators/latest-release, 
5625.0,Economy,Business Indicators,Private New Capital Expenditure And Expected Expenditure Australia,https://www.abs.gov.au/statistics/economy/business-indicators/private-new-capital-expenditure-and-expected-expenditure-australia/latest-release, 
5655.0,Economy,Finance,Managed Funds Australia,https://www.abs.gov.au/statistics/economy/finance/managed-funds-australia/latest-release, 
5676.0,Economy,Business Indicators,Business Indicators Australia,https://www.abs.gov.au/statistics/economy/business-indicators/business-indicators-australia/latest-release, 
5681.0,Economy,Business Indicators,Monthly Business Turnover Indicator,https://www.abs.gov.au/statistics/economy/business-indicators/monthly-business-turnover-indicator/latest-release, 
5682.0,Economy,Finance,Monthly Household Spending Indicator,https://www.abs.gov.au/statistics/economy/finance/monthly-household-spending-indicator/latest-release, 
6202.0,Labour,Employment And Unemployment,Labour Force Australia,https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/latest-release, 
6150.0.55.003,Labour,Labour Accounts,Labour Account Australia,https://www.abs.gov.au/statistics/labour/labour-accounts/labour-account-australia/latest-release, 
6248.0.55.002,Labour,Employment And Unemployment,Public Sector Employment And Earnings,https://www.abs.gov.au/statistics/labour/employment-and-unemployment/public-sector-employment-and-earnings/latest-release, 
6291.0.55.001,Labour,Employment And Unemployment,Labour Force Australia Detailed,https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/latest-release, 
6302.0,Labour,Earnings And Working Conditions,Average Weekly Earnings Australia,https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/average-weekly-earnings-australia/latest-release, 
6321.0.55.001,Labour,Earnings And Working Conditions,Industrial Disputes Australia,https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/industrial-disputes-australia/latest-release, 
6345.0,Economy,Price Indexes And Inflation,Wage Price Index Australia,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/wage-price-index-australia/latest-release, 
6354.0,Labour,Jobs,Job Vacancies Australia,https://www.abs.gov.au/statistics/labour/jobs/job-vacancies-australia/latest-release, 
6401.0,Economy,Price Indexes And Inflation,Consumer Price Index Australia,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release, 
6416.0,Economy,Price Indexes And Inflation,Residential Property Price Indexes Eight Capital Cities,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/residential-property-price-indexes-eight-capital-cities/latest-release,Ceased
6427.0,Economy,Price Indexes And Inflation,Producer Price Indexes Australia,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/producer-price-indexes-australia/latest-release, 
6432.0,Economy,Price Indexes And Inflation,Total Value Dwellings,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings/latest-release, 
6457.0,Economy,Price Indexes And Inflation,International Trade Price Indexes Australia,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/international-trade-price-indexes-australia/latest-release, 
6467.0,Economy,Price Indexes And Inflation,Selected Living Cost Indexes Australia,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/selected-living-cost-indexes-australia/latest-release, 
6484.0,Economy,Price Indexes And Inflation,Monthly Consumer Price Index Indicator,https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/monthly-consumer-price-index-indicator/latest-release, 
7215.0,Industry,Agriculture,Livestock Products Australia,https://www.abs.gov.au/statistics/industry/agriculture/livestock-products-australia/latest-release, 
7218.0.55.001,Industry,Agriculture,Livestock And Meat Australia,https://www.abs.gov.au/statistics/industry/agriculture/livestock-and-meat-australia/latest-release,Ceased
8155.0,Industry,Industry Overview,Australian Industry,https://www.abs.gov.au/statistics/industry/industry-overview/australian-industry/latest-release, 
8165.0,Economy,Business Indicators,Counts Australian Businesses Including Entries And Exits,https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release, 
8412.0,Industry,Mining,Mineral And Petroleum Exploration Australia,https://www.abs.gov.au/statistics/industry/mining/mineral-and-petroleum-exploration-australia/latest-release, 
8501.0,Industry,Retail And Wholesale Trade,Retail Trade Australia,https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade/retail-trade-australia/latest-release, 
8701.0,Industry,Building And Construction,Estimated Dwelling Stock,https://www.abs.gov.au/statistics/industry/building-and-construction/estimated-dwelling-stock/latest-release, 
8731.0,Industry,Building And Construction,Building Approvals Australia,https://www.abs.gov.au/statistics/industry/building-and-construction/building-approvals-australia/latest-release, 
8752.0,Industry,Building And Construction,Building Activity Australia,https://www.abs.gov.au/statistics/industry/building-and-construction/building-activity-australia/latest-release, 
8755.0,Industry,Building And Construction,Construction Work Done Australia Preliminary,https://www.abs.gov.au/statistics/industry/building-and-construction/construction-work-done-australia-preliminary/latest-release, 
8762.0,Industry,Building And Construction,Engineering Construction Activity Australia,https://www.abs.gov.au/statistics/industry/building-and-construction/engineering-construction-activity-australia/latest-release, 
8782.0.65.001,Industry,Building And Construction,Construction Activity Chain Volume Measures Australia,https://www.abs.gov.au/statistics/industry/building-and-construction/construction-activity-chain-volume-measures-australia/jun-2020,Ceased
"""
    return read_csv(StringIO(csv), index_col=0)
