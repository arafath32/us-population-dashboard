# U.S. Population Dashboard 

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


# 1. Page Setup

st.set_page_config(page_title="US Population Dashboard ", layout="wide")

st.title("US Population Dashboard")
st.caption("Follow the 4 pillars: Connect → Clean → Design → Develop")


# 2. Connect — Load Data

@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path)
    # Expect: states, id, 2010..2019
    df.columns = df.columns.str.strip().str.title()  # States, Id, 2010..2019
    df["Id"] = df["Id"].astype(int)

    # Wide -> Long (Year, Population)
    df = df.melt(
        id_vars=["States", "Id"],
        var_name="Year",
        value_name="Population"
    )
    df["Year"] = df["Year"].astype(int)
    df["Population"] = df["Population"].astype(str).str.replace(",", "", regex=False).astype(float)
    return df


DATA_PATH = r"C:\Users\itz_MFz\Desktop\DASHBOARD\us-population-2010-2019.csv"
df = load_data(DATA_PATH)

# 3. Clean — Sidebar Filters

st.sidebar.header("US Population Dashboard")

min_year = int(df["Year"].min())
max_year = int(df["Year"].max())

year_selected = st.sidebar.selectbox(
    "Select a Year",
    list(range(min_year, max_year + 1)),
    index=(max_year - min_year)
)
color_theme = st.sidebar.selectbox("Select Color Theme", ["blues", "greens", "reds"])

# Filtered DataFrame
fdf = df[df["Year"] == year_selected].copy()

# Previous year for deltas
prev_year = year_selected - 1
prev_df = df[df["Year"] == prev_year][["States", "Population"]].rename(
    columns={"Population": "Population_prev"}
)
fdf = fdf.merge(prev_df, on="States", how="left")


# 4. KPI Cards — Gains / Losses Summary

def fmt_millions(x):
    return f"{x/1_000_000:.1f} M"

def fmt_delta_k(x):
    if pd.isna(x):
        return "—"
    return f"{x/1_000:+,.0f} K"  # show +/− in thousands

st.subheader("Gains / Losses")
kpi1, kpi2 = st.columns(2)

top_state = fdf.loc[fdf["Population"].idxmax()]
low_state = fdf.loc[fdf["Population"].idxmin()]

top_delta = top_state["Population"] - top_state["Population_prev"] if pd.notna(top_state["Population_prev"]) else np.nan
low_delta = low_state["Population"] - low_state["Population_prev"] if pd.notna(low_state["Population_prev"]) else np.nan

kpi1.metric(top_state["States"], fmt_millions(top_state["Population"]), fmt_delta_k(top_delta))
kpi2.metric(low_state["States"], fmt_millions(low_state["Population"]), fmt_delta_k(low_delta))

st.divider()


# 5. Charts — Design & Develop 

left, mid, right = st.columns([1.1, 1.8, 1.2], gap="large")

# --- Left: States Migration ---
with left:
    st.subheader("States Migration")
    inbound_pct, outbound_pct = 27, 2  
    def donut_chart(label, percent, color):
        src = pd.DataFrame({"segment": ["value", "rest"], "val": [percent, 100 - percent]})
        ring = alt.Chart(src).mark_arc(innerRadius=44, outerRadius=62).encode(
            theta="val:Q",
            color=alt.Color("segment:N", scale=alt.Scale(range=[color, "#E6E6E6"]), legend=None),
        ).properties(width=150, height=150)
        # White text so it’s visible
        txt = alt.Chart(pd.DataFrame({"t": [f"{int(percent)} %"]})).mark_text(
            fontSize=18, fontWeight="bold", color="white"
        ).encode(text="t:N")
        lbl = alt.Chart(pd.DataFrame({"l": [label]})).mark_text(
            dy=46, color="white", opacity=0.95
        ).encode(text="l:N")
        return ring + txt + lbl

    d1, d2 = st.columns(2)
    d1.altair_chart(donut_chart("Inbound", inbound_pct, "#22c55e"), use_container_width=False)
    d2.altair_chart(donut_chart("Outbound", outbound_pct, "#ef4444"), use_container_width=False)

#  Middle: Heatmap 
with mid:
    st.subheader("States Migration Overview")
    heat_df = (
        df.pivot(index="Year", columns="States", values="Population")
        .fillna(0)
        .reset_index()
        .melt("Year", var_name="State", value_name="Population")
    )
    heat_chart = alt.Chart(heat_df).mark_rect().encode(
        x=alt.X("State:N", sort=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y("Year:O", title="Year"),
        color=alt.Color("Population:Q", scale=alt.Scale(scheme=color_theme)),
        tooltip=["Year:O", "State:N", alt.Tooltip("Population:Q", format=",.0f")]
    ).properties(height=300)
    st.altair_chart(heat_chart, use_container_width=True)

# Right: Top States 
with right:
    st.subheader(f"Top States ({year_selected})")
    top10 = fdf.sort_values("Population", ascending=False).head(10)

    lines = alt.Chart(top10).mark_rule(color="#ef4444", strokeWidth=8).encode(
        y=alt.Y("States:N", sort="-x", title="States"),
        x=alt.X("Population:Q", title="Population"),
        x2=alt.value(0),
        tooltip=[alt.Tooltip("Population:Q", format=",.0f"), "States:N"]
    ).properties(height=360)

    labels = alt.Chart(top10).mark_text(align="left", dx=6).encode(
        y=alt.Y("States:N", sort="-x"),
        x="Population:Q",
        text=alt.Text("Population:Q", format=",.0f")
    )

    st.altair_chart(lines + labels, use_container_width=True)


# 6. Raw Data + Download Option

with st.expander("Show Filtered Data"):
    st.dataframe(
        fdf[["States", "Id", "Year", "Population"]].sort_values("Population", ascending=False),
        use_container_width=True
    )
    st.download_button(
        "Download filtered data as CSV",
        data=fdf.to_csv(index=False),
        file_name=f"filtered_population_{year_selected}.csv"
    )


# 7. Footer — Info

st.caption("""
About:

U.S. Census Bureau
           
Gains/Losses: highest/lowest state for the selected year (2010 to 2019)
           
States Migration: demo rings and heatmap.
""")