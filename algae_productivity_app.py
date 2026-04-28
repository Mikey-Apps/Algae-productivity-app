import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go 
from scipy.stats import linregress

st.set_page_config(layout = "wide")
st.title("Algae metabolite production")
st.markdown("""
Estimate annual productivity of a metabolite from 1L of cultivated algae.∏
""")

#---------------------------------------------------------------#
#User inputs
#---------------------------------------------------------------#
st.subheader("Input")

#create default reference samples
def default_samples():
    return pd.DataFrame([
            {"sample name": "Algae_strain1", "Algae dry biomass productivity (g/L)": 1.0, "%Metabolite from biomass": 2.00, "Days to harvest": 7.0},
            {"sample name": "Algae_strain2", "Algae dry biomass productivity (g/L)": 0.9, "%Metabolite from biomass": 0.45, "Days to harvest": 13.0}
        ])

with st.form("samples_form", clear_on_submit=False):
    #User variables    
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.subheader("Variables")
        metabolite = st.text_input("Metabolite name", value = "Metabolite")
    with col2:
        st.subheader("")        
        #bioreactor_size = st.number_input("Bioreactor size (L)", value = 100)

    if "samples_df" not in st.session_state:
        st.session_state.samples_df = default_samples()

    required_cols = ["sample name", "Algae dry biomass productivity (g/L)", "%Metabolite from biomass", "Days to harvest"]

    #User samples
    st.subheader("Samples")
    edited_df = st.data_editor(
        st.session_state.samples_df,
        num_rows="dynamic",
        hide_index=True,
        key="samples_editor"
    )
    submitted_samples = st.form_submit_button("Submit")

if submitted_samples:
    clean_df = edited_df.dropna(subset=required_cols).reset_index(drop=True)

    if clean_df.empty:
        st.error("Please fill in at least one complete sample.")
        st.stop()

    st.session_state.samples_df = clean_df

#---------------------------------------------------------------#
#create plots
#---------------------------------------------------------------#
def annual_calculation(sample_data):
    harvest_days = np.arange(sample_data["Days to harvest"], 366, sample_data["Days to harvest"])
    harvest_number = np.arange( 1, len(harvest_days)+1 )    
    #create new dataframe 
    df =pd.DataFrame({
        "harvest#": harvest_number,
        "harvest_day": harvest_days
        })
    #calculate biomass and compound content from these values
    df["Algae_biomass(g)"] = sample_data["Algae dry biomass productivity (g/L)"]
    df["harvested_metabolite(g)"] = df["Algae_biomass(g)"] * sample_data["%Metabolite from biomass"] * 0.01
    df["cumulative_metabolite_total"] = df["harvested_metabolite(g)"].cumsum()
    df["sample"] = sample_data["sample name"]
    return(df)

#calculate annual compound production for each sample
results_all = []
for idx, row in edited_df.iterrows():
     df = annual_calculation(row)
     results_all.append(df)
results_all = dict( zip( edited_df["sample name"], results_all ))

#make figure
fig = go.Figure()
for sample_name in results_all.keys():
    sample_df = results_all[sample_name]

    fig.add_trace(
        go.Scatter(
            x=sample_df["harvest_day"],
            y=sample_df["cumulative_metabolite_total"],
            mode="markers",
            name=sample_name,
            marker=dict(size=7, opacity=0.9),
            customdata=sample_df[["harvest#"]],
            hovertemplate=(
                f"Sample: {sample_name}<br>"
                "Harvest#: %{customdata[0]}<br>"
                "Day: %{x}<br>"
                f"Cumulative total: %{{y}}<extra></extra>"
            ),
        )
    )

fig.update_layout(
    #template="plotly_white",
    plot_bgcolor="white",
    #paper_bgcolor="white",
    title=f"Annual {metabolite} production",
    title_font=dict(size = 30),
    xaxis_title="Day",
    yaxis_title=f"Cumulative {metabolite} production (g/L Algae)",
    legend_title="Sample",    
    height=600,
)
fig.update_xaxes(
    tickmode="array",
    tickvals=np.arange(0, 366, 30),
    tickangle=270,
    title_font=dict(size=26),
    tickfont=dict(size=18)
)
fig.update_yaxes(
    tickmode="array",
    title_font=dict(size=20),
    tickfont=dict(size=18)
)
fig.add_vline(
    x=365,
    line_width = 2,
    line_dash = "dash",
    line_color = "black"
)
st.plotly_chart(fig, width = "stretch", theme = None)


#---------------------------------------------------------------#
#Summary table
#---------------------------------------------------------------#
#Display annual production estimates
def annual_production(df):
    #fit to regression line
    reg = linregress(df["harvest_day"], df["cumulative_metabolite_total"])
    #estimate x on day 365
    y_365 = reg.slope *365 + reg.intercept
    return {
        "annual algae harvests": df["harvest#"].iloc[-1],
        "date of final harvest": df["harvest_day"].iloc[-1],
        "realized annual metabolite production (g)": df["cumulative_metabolite_total"].iloc[-1],
        "estimated annual metabolite production (g) - normalized to 365 days": y_365
    }
 
annual_estimations = {sample: annual_production(df) for sample, df in results_all.items() }
annual_summary = pd.DataFrame(annual_estimations).T.reset_index()
annual_summary["annual algae harvests"] = annual_summary["annual algae harvests"].astype(int)
annual_summary["date of final harvest"] = annual_summary["date of final harvest"].astype(int)
annual_summary.rename( columns= {"index":"sample"}, inplace=True)

st.header("Annual productivity from 1L algae")
st.dataframe(annual_summary, hide_index=True)
