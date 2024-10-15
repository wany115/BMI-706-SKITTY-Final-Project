import altair as alt
import pandas as pd
import streamlit as st
# import seaborn as sns
# import matplotlib.pyplot as plt

# Show the page title and description.
st.set_page_config(page_title="Socioeconomic Factors & COVID19")
st.title("Socioeconomic Factors & COVID19")
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
    df = pd.read_csv("data/plot2.csv")
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

# Create a bar chart showing the raw cases for the filtered countries
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
    labelFontSize=10  # Set the font size for the x-axis labels
)

# Display the bar chart
st.altair_chart(bar_chart, use_container_width=True)


