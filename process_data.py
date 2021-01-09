import pandas as pd

df2 = pd.read_csv("/Users/shivaninanda/Desktop/COVID_Grapher/us-counties.csv")

fips_df = pd.read_csv('/Users/shivaninanda/Desktop/COVID_Grapher/co-est2019-alldata.csv')
fips_df['fips'] = fips_df.apply(lambda x: "%02d%03d" % (x.STATE, x.COUNTY), axis = 1)


#df2.fips = df2.fips.astype('object')
fips_df = fips_df[['fips', 'POPESTIMATE2019']]
fips_df.fips = fips_df.fips.astype('int64')

df2 = df2.loc[lambda x: x.county != "Unknown"]
# print(set(df2.loc[~np.isfinite(df2.fips)].county.tolist()))
# set(['New York City', 'Joplin', 'Kansas City'])
df2.fips = df2.fips.fillna(-1).astype('int64')


df2 = df2.merge(fips_df, how = 'left', on=['fips'])
#print(df2.head())
df2['date']= pd.to_datetime(df2['date'])

df2.loc[df2.county == 'New York City', 'POPESTIMATE2019'] = 8.339 * 10e6
df2.loc[df2.county == 'Joplin', 'POPESTIMATE2019'] = 50657
df2.loc[df2.county == 'Kansas City', 'POPESTIMATE2019'] = 491918

def cumulativeToDaily(df):
    #dfDaily = df.sort_values(by=['date'])
    dfDaily = df.groupby("date").agg({
        "deaths":"sum", 
        "cases":"sum", 
        "POPESTIMATE2019":"first"
    })
    dfDaily["daily_cases"] = dfDaily.cases - dfDaily.cases.shift(1)
    dfDaily["daily_deaths"] = dfDaily.deaths - dfDaily.deaths.shift(1)

    for value in ["cases", "deaths", "daily_cases", "daily_deaths"]:
        dfDaily[value + "_rate"] = dfDaily[value] / dfDaily.POPESTIMATE2019
    dfDaily = dfDaily.fillna(0)
    return dfDaily

df2 = df2.groupby(["state", "county"]).apply(cumulativeToDaily).reset_index()
df2['date']= pd.to_datetime(df2['date'])

df2.to_csv('/Users/shivaninanda/Desktop/COVID_Grapher/daily_cases_data.csv', index = False)