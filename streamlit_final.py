import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from epiweeks import Week
from datetime import datetime

st.set_page_config(page_title="COVID-19 Time Series Data & Socioeconomic Factors")
st.title("Global COVID-19 Data & Socioeconomic Factors in 2020")
st.write(
    """
    Our visualization aims at informing non-experts of trends of COVID-19 pandemic development in 2020. 
    We work on country-level data across 2020 and explore temporal/geographical trends in below. 
    To allow for more nuanced insights, we also incorporate socioeconomic factors with annual COVID-19 data counts. 
    Enjoy your visit, and stay safe!
    """
)

# Section 1: COVID-19 Data Analysis
url="https://raw.githubusercontent.com/wany115/BMI-706-SKITTY-Final-Project/refs/heads/main/Cleaned%20Data/Weekly%20Data.csv"
df1 = pd.read_csv(url)
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

st.header("Part 1: Worldwide COVID-19 Weekly Cases in 2020")
st.write(
    """
    This section focuses on COVID-19 data from Johns Hopkins University. 
    It provides insights into worldwide COVID-19 weekly cases across 2020, 
    including trends and comparisons between countries.
    """
)

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

# Spacer
st.markdown("---")
st.header("Part 2: Socioeconomic Factors & COVID-19 Interaction")
st.write(
    """
    This app visualizes COVID data from Johns Hopkins University and Socioeconomic data 
    from World Bank Health Nutrition and Population Statistics. 
    It shows how the socioeconomic factors interact with COVID rates for each country. 
    Just click on the widgets below to explore!
    """
)


# Load the data from a CSV
@st.cache_data
def load_data():
    df = pd.read_csv("https://raw.githubusercontent.com/wany115/BMI-706-SKITTY-Final-Project/refs/heads/main/Cleaned%20Data/plot2.csv")
    return df


df = load_data()

# rename columns
df.columns = ['country', 'health_expenditure', 'death_rate','GDP','life_expectancy','literacy_rate','net_migration',
              'poverty_ratio','unemployment','population','density','confirmed','deaths','recovered','active']
# calculate ratios
df['covid_confirmed_ratio'] = df['confirmed'] / df['population']
df['covid_deaths_ratio'] = df['deaths'] / df['population']
df['covid_recovered_ratio'] = df['recovered'] / df['population']
df['covid_active_ratio'] = df['active'] / df['population']

# Dropdown for selecting the X and Y factors
x_axis = st.selectbox('Select X-axis factor (Used for scatterplot and bar chart)', 
                      options=['health_expenditure', 'death_rate', 'GDP', 'life_expectancy', 'literacy_rate', 'net_migration', 'poverty_ratio', 'unemployment'],
                      index=0) # default heath_expenditure
y_axis = st.selectbox('Select Y-axis factor', 
                      options=['health_expenditure', 'death_rate', 'GDP', 'life_expectancy', 'literacy_rate', 'net_migration', 'poverty_ratio', 'unemployment'],
                      index = 2) # default GDP

# Dropdown for selecting the ratio category (confirmed, active, deaths, recovered)
ratio_category = st.selectbox(
    'Ratio category',
    options=['covid_confirmed_ratio', 'covid_active_ratio', 'covid_deaths_ratio', 'covid_recovered_ratio'],
    format_func=lambda x: x.replace('_', ' ').title(),
    index=0  # Set default to 'confirmed_ratio
)

# Dropdown for selecting countries
countries = st.multiselect('Country', 
                           options=df['country'].unique(), 
                           default=df['country'].unique())

# Filter data based on selected countries
filtered_df = df[df['country'].isin(countries)]

# Section 1: Bubble Chart
st.header("Bubble Chart: COVID-19 Ratio by Socioeconomic Factors")

# Create the bubble chart
bubble_chart = alt.Chart(filtered_df).mark_circle().encode(
    x=alt.X(x_axis, title=x_axis.replace('_', ' ').title()),
    y=alt.Y(y_axis, title=y_axis.replace('_', ' ').title()),
    size=alt.Size(ratio_category, title=ratio_category.replace('_', ' ').title(), scale=alt.Scale(range=[100, 1000])),
    color=alt.Color('country', legend=None),
    tooltip=['country', ratio_category, x_axis, y_axis]
).properties(
    width=700,
    height=500,
    title=f'Bubble Chart: {x_axis.replace("_", " ").title()} vs {y_axis.replace("_", " ").title()} (Size: {ratio_category.replace("_", " ").title()})'
)

# Display the bubble chart
st.altair_chart(bubble_chart, use_container_width=True)

st.caption("COVID ratio are total cases per country in 2020 divided by population. For instance: covid confirmed ratio = confirmed cases/population")

#########################################################################################################
# Section 2: Scatterplot + Regression Line
st.header("Scatterplot + Regression Line")

# Calculate the correlation coefficient between the selected socioeconomic factor and the selected COVID ratio
correlation_coef = filtered_df[x_axis].corr(filtered_df[ratio_category])

# Create the scatterplot with a regression line
scatter_plot = alt.Chart(filtered_df).mark_circle(size=100).encode(
    x=alt.X(x_axis, title=x_axis.replace('_', ' ').title()),
    y=alt.Y(ratio_category, title=ratio_category.replace('_', ' ').title()),
    color=alt.Color('country', legend=None),
    tooltip=['country', x_axis, ratio_category]
)

# Add the regression line with slope and intercept in the tooltip
regression_line = scatter_plot.transform_regression(
    x_axis, ratio_category
).mark_line(color='red').encode(
    tooltip=[
        alt.Tooltip('slope:Q', title='Slope'),
        alt.Tooltip('intercept:Q', title='Intercept')
    ]
)

# Layer the scatterplot and regression line, and set the combined title
final_chart = alt.layer(
    scatter_plot + regression_line
).properties(
    width=700,
    height=500,
    title={
        'text': f'Scatterplot: {x_axis.replace("_", " ").title()} vs {ratio_category.replace("_", " ").title()}',
        'subtitle': f'Correlation: {correlation_coef:.2f}'
    }
).configure_title(
    anchor='start',
    fontSize=16,
    fontWeight='bold',
    subtitleFontSize=16,  # Subtitle styling
    subtitleFontWeight='normal',
    lineHeight=25  # Adjust title-subtitle spacing
)

# Display the final combined chart (scatterplot + regression line + correlation text as title)
st.altair_chart(final_chart, use_container_width=True)

#########################################################################################################
# Section 3: Heatmap of correlations
st.header("Heatmap: correlations")
# Select columns for the correlation matrix
correlation_columns = ['health_expenditure', 'death_rate', 'GDP', 'life_expectancy', 'literacy_rate', 'net_migration', 
                       'poverty_ratio', 'unemployment', 'population', 'density', 
                       'covid_confirmed_ratio', 'covid_deaths_ratio', 'covid_recovered_ratio', 'covid_active_ratio']

# Calculate the correlation matrix
correlation_matrix = df[correlation_columns].corr()

# Convert the correlation matrix to a long format suitable for Altair
correlation_long = correlation_matrix.reset_index().melt(id_vars='index')
correlation_long.columns = ['Variable 1', 'Variable 2', 'Correlation']

# Create the heatmap with Altair
heatmap = alt.Chart(correlation_long).mark_rect().encode(
    x=alt.X('Variable 1:N', title='Socioeconomic Factors and COVID-19 Metrics'),
    y=alt.Y('Variable 2:N', title='Socioeconomic Factors and COVID-19 Metrics'),
    color=alt.Color('Correlation:Q', scale=alt.Scale(scheme='redblue')),
    tooltip=['Variable 1', 'Variable 2', 'Correlation']
).properties(
    width=600,
    height=600,
    title="Correlation Heatmap"
)

# Display the heatmap in Streamlit
st.altair_chart(heatmap, use_container_width=True)

############################################################################################
# Section 4: Bar chart
st.header("Bar chart: Raw cases filtered by socioeconomic factors")

# Dropdown for case type (confirmed, active, deaths, recovered)
case_type = st.selectbox(
    'Case Type',
    options=['confirmed', 'active', 'deaths', 'recovered'],
    format_func=lambda x: x.capitalize()
)

# Slider for filtering countries based on the selected socioeconomic factor
min_value = float(df[x_axis].min())
max_value = float(df[x_axis].max())

factor_range = st.slider(
    f'Select Range for {x_axis.replace("_", " ").title()}',
    min_value=min_value,
    max_value=max_value,
    value=(min_value, max_value)  # Default range is the full range of the data
)

# Filter the dataset based on the selected socioeconomic factor range
filtered_range_df = df[(df[x_axis] >= factor_range[0]) & (df[x_axis] <= factor_range[1])]

# Add a checkbox for log10 scale
is_log10_bar = st.checkbox("log10 scale for bar chart")

# Create a bar chart showing the raw cases for the filtered countries with log10 option
if is_log10_bar:
    bar_chart = alt.Chart(filtered_range_df).mark_bar().encode(
        x=alt.X('country:N', title='Country', sort=alt.EncodingSortField(field=case_type, order='descending')),
        y=alt.Y(f'{case_type}:Q', title=f'log10 Total {case_type.capitalize()} Cases', 
                scale=alt.Scale(type='log', base=10)),
        color=alt.Color('country:N', legend=None),
        tooltip=['country', f'{case_type}', x_axis]
    ).properties(
        width=700,
        height=500,
        title=f'Total {case_type.capitalize()} Cases by Country (Filtered by {x_axis.replace("_", " ").title()})'
    )
else:
    bar_chart = alt.Chart(filtered_range_df).mark_bar().encode(
        x=alt.X('country:N', title='Country', sort=alt.EncodingSortField(field=case_type, order='descending')),
        y=alt.Y(f'{case_type}:Q', title=f'Total {case_type.capitalize()} Cases'),
        color=alt.Color('country:N', legend=None),
        tooltip=['country', f'{case_type}', x_axis]
    ).properties(
        width=700,
        height=500,
        title=f'Total {case_type.capitalize()} Cases by Country (Filtered by {x_axis.replace("_", " ").title()})'
    ).configure_axisX(
        labelFontSize=10
    )

# Display the bar chart
st.altair_chart(bar_chart, use_container_width=True)
