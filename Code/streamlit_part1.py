import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from epiweeks import Week
from datetime import datetime

df1 = pd.read_csv(r"C:\Users\Dailin LUO\BMI706FP\Weekly Data.csv")
df1['country-code'] = df1['country-code'].astype(str).str.zfill(3)
df1 = df1.iloc[:,:-7]
df1['Confirmed_per_100k'] = (df1['Confirmed'] / df1['Population']) * 100000
df1['Deaths_per_100k'] = (df1['Deaths'] / df1['Population']) * 100000
df1['Recovered_per_100k'] = (df1['Recovered'] / df1['Population']) * 100000
df1['Active_per_100k'] = (df1['Active'] / df1['Population']) * 100000
df1['Confirmed_per_km2'] = df1['Confirmed'] / df1['Population'] * df1['Density (P/Km²)']
df1['Deaths_per_km2'] = df1['Deaths'] / df1['Population'] * df1['Density (P/Km²)']
df1['Recovered_per_km2'] = df1['Recovered'] / df1['Population'] * df1['Density (P/Km²)'] 
df1['Active_per_km2'] = df1['Active'] / df1['Population'] * df1['Density (P/Km²)'] 
case_columns = {
    'Confirmed': ['Confirmed', 'Confirmed_per_100k', 'Confirmed_per_km2'],
    'Deaths': ['Deaths', 'Deaths_per_100k', 'Deaths_per_km2'],
    'Recovered': ['Recovered', 'Recovered_per_100k', 'Recovered_per_km2'],
    'Active': ['Active', 'Active_per_100k', 'Active_per_km2']
}

df1_long = pd.DataFrame()
for key, cols in case_columns.items():
    melted = pd.melt(df1, 
                     id_vars=['Country_Region', 'country-code','Population', 'Density (P/Km²)', 'Week_Start_Date', 'MMWR_week'],
                     value_vars=cols, 
                     var_name='Case_Type', 
                     value_name='Case')  # Use a generic value name
    
    melted['Case_Category'] = melted['Case_Type'].map({
        cols[0]: 'Weekly Case',
        cols[1]: 'Weekly Case per 100k',
        cols[2]: 'Weekly Case per km2'
    })
    
    # Add a new column for the metric (Confirmed, Deaths, etc.)
    melted['Metric'] = key
    
    # Append to the main dataframe
    df1_long = pd.concat([df1_long, melted], ignore_index=True)

from vega_datasets import data
source = alt.topo_feature(data.world_110m.url, 'countries')

width = 600
height  = 300
project = 'equirectangular'

# a gray map using as the visualization background
background = alt.Chart(source
).mark_geoshape(
    fill='#aaa',
    stroke='white'
).properties(
    width=width,
    height=height
).project(project)

st.write("## Worldwide COVID-19 Weekly Cases in 2020")

def get_mmwr_week(date):
    return Week.fromdate(date).week

start_date, end_date = st.slider("Select a range of date", 
                                 datetime(2020, 1, 1).date(), datetime(2020, 12, 31).date(), 
                                 (datetime(2020, 1, 1).date(), datetime(2020, 12, 31).date()))
start_mmwr_week = get_mmwr_week(start_date)
end_mmwr_week = get_mmwr_week(end_date)
df1_date = df1_long[(df1_long['MMWR_week'] >= start_mmwr_week) & (df1_long['MMWR_week'] <= end_mmwr_week)]

countries = st.multiselect("Countries (at most 7)", options=df1["Country_Region"].unique(), 
                           default=["Canada", "Nigeria", "Iceland", "Russia", "Sweden", "China", "US"],
                           max_selections = 7) 
df1_date_ctry = df1_date[df1_date["Country_Region"].isin(countries)]

metric = st.selectbox("Metric",options=df1_long["Metric"].unique()) 
df1_date_ctry_metric = df1_date_ctry[df1_date_ctry["Metric"] == metric]

case_cat = st.radio("Case Unit",options=df1_long["Case_Category"].unique())
df1_date_ctry_metric_casecat = df1_date_ctry_metric[df1_date_ctry_metric["Case_Category"]==case_cat]

mean_case_data = df1_date_ctry_metric_casecat.groupby(['Country_Region', 'country-code'], as_index=False).agg({'Case': 'mean'})

chart_map = alt.Chart(source
    ).mark_geoshape().encode(
        # color=alt.Color(field='Case', type='quantitative', scale = case_scale, legend=alt.Legend(title='Quartiles', labelFontSize=6)),        
        color=alt.Color('Case:Q', scale=alt.Scale(scheme="yelloworangebrown")),
        tooltip=[
            alt.Tooltip('Country_Region:N'),
            alt.Tooltip('Case:Q') 
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(mean_case_data, 'country-code', ['Country_Region','Case']),
    ).properties(
        title=f'Average {case_cat} of {metric}'
    )

(background + chart_map)

is_log10 = st.checkbox("log10 scale")
if is_log10:
    chart_line = alt.Chart(df1_date_ctry_metric_casecat).mark_line(point=True).encode(
        x = alt.X("Week_Start_Date:T", title = 'Week'),
        y = alt.Y("Case:Q", scale=alt.Scale(type='log', base=10), title = f'log10 {case_cat}'),
        color=alt.Color(field = 'Country_Region'),
        tooltip = [alt.Tooltip('Country_Region:N'), alt.Tooltip('Week_Start_Date:T'), alt.Tooltip('Case:Q')]
    ).properties(
        title=f'{case_cat} of {metric}',
        width = 600,
        height = 400
    )
else:
    chart_line = alt.Chart(df1_date_ctry_metric_casecat).mark_line(point=True).encode(
        x = alt.X("Week_Start_Date:T", title = 'Week'),
        y = alt.Y("Case:Q", title = case_cat),
        color=alt.Color(field = 'Country_Region'),
        tooltip = [alt.Tooltip('Country_Region:N'), alt.Tooltip('Week_Start_Date:T'), alt.Tooltip('Case:Q')]
    ).properties(
        title=f'{case_cat} of {metric}',
        width = 600,
        height = 400
    )
chart_line