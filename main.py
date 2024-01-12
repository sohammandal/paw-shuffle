import streamlit as st
import requests
import pandas as pd
import re
import time
from PIL import Image
from io import BytesIO
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(page_title="Paw Shuffle", page_icon="🐶", layout="wide")
st.title("Paw Shuffle 🐶")

def read_and_process_csv():
    """Read CSV and perform transformations"""

    df = pd.read_csv("akc-data-latest.csv")
    df["breed_lower"] = df["breed"].str.lower()
    df["average_weight"] = (df["min_weight"] + df["max_weight"]) / 2
    df["average_height"] = (df["min_height"] + df["max_height"]) / 2
    df["average_expectancy"] = (df["min_expectancy"] + df["max_expectancy"]) / 2
    return df

def request_dog_api_data():
    """Makes GET request to https://dog.ceo/dog-api/ to fetch a random dog image URL"""

    response = requests.get("https://dog.ceo/api/breeds/image/random")
    if response.status_code == 200:
        data = response.json()
        return data.get("message")
    else:
        return None

def extract_breed_name(url):
    """Use regex to extract breed name from URL"""

    print(f"API URL: {url}")
    pattern = r"https:\/\/images\.dog\.ceo\/breeds\/([\w-]+)\/"
    match = re.search(pattern, url)
    if match:
        breed_name = match.group(1)
        if "-" in breed_name:
            breed_name = " ".join(reversed(breed_name.split("-")))
        return breed_name
    else:
        return None

def search_breed_in_dataframe(df, breed_name):
    """Search for an exact or wildcard match in CSV data"""
    
    exact_match = df[df["breed_lower"] == breed_name]
    if not exact_match.empty:
        return exact_match.iloc[0]

    contains_match = df[df["breed_lower"].str.contains(breed_name, case=False, regex=False)]
    if not contains_match.empty:
        return contains_match.iloc[0]

    return None

def display_charts(df_result):
    """Create a 2x2 grid for comparison plots"""
    fig = make_subplots(rows=2, cols=2, subplot_titles=["Height", "Weight", "Expectancy", "Shedding"])

    # Chart 1: Height Distribution
    fig.add_trace(
        px.histogram(df, x="average_height", barmode="group").data[0], row=1, col=1
    )

    # Chart 2: Weight Distribution
    fig.add_trace(
        px.histogram(df, x="average_weight", barmode="group").data[0], row=1, col=2
    )

    # Chart 3: Expectancy Distribution
    fig.add_trace(
        px.bar(df, x="average_expectancy", orientation="v").data[0], row=2, col=1
    )

    # Chart 4: Shedding Distribution
    fig.add_trace(
        px.histogram(df, x="shedding_category", barmode="group").data[0], row=2, col=2
    )

    fig.update_xaxes(
        categoryorder="array",
        categoryarray=["Infrequent", "Occasional", "Seasonal", "Regularly", "Frequent"],
        row=2,
        col=2,
    )

    loop_object = [['average_height', 1, 1],
                   ['average_weight', 1, 2],
                   ['average_expectancy', 2, 1],
                   ['shedding_category', 2, 2],]

    # Add annotations to each chart
    for i in loop_object:
        fig.add_annotation(
            x=df_result[i[0]],
            y=0,
            text=f'{df_result["breed"]}',
            showarrow=True,
            arrowhead=4,
            ax=0,
            ay=-40,
            arrowcolor="red",
            font=dict(color="black", size=12),
            bgcolor="white",
            row=i[1],
            col=i[2],
        )

    fig.update_layout(height=900, width=900)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

def main():
    """Main logic to fetch random dog image from API, join with CSV to extract breed information, and make comparison plots"""

    col1, col2, col3 = st.columns([0.3, 0.05, 0.65])

    with col1:
        # Keep trying the URL until valid match
        while True:
            image_url = request_dog_api_data()
            breed_name = extract_breed_name(image_url)

            if breed_name:
                df_result = search_breed_in_dataframe(df, breed_name)
                if df_result is not None:
                    break  # Exit loop if a valid breed is found in the CSV
                else:
                    print(f"Could not find breed: {breed_name}")

        print(f"URL breed: {breed_name} and CSV breed: {df_result['breed']}")
        
        # Display breed name and image
        st.subheader(df_result["breed"])
        if image_url:
            image_response = requests.get(image_url)

            if image_response.status_code == 200:
                image = Image.open(BytesIO(image_response.content))
                st.image(image, caption=df_result["breed"], use_column_width='auto')
            else:
                st.error(f"Error code: {image_response.status_code}")
        else:
            st.error("Failed to fetch data")

        # Display breed information
        with st.expander("See Description"):
            st.markdown(f"{df_result['description']}")
        st.markdown(f"**Group:** {df_result['group']}")
        st.markdown(f"**Temperament:** {df_result['temperament']}")
        st.markdown(f"**Trainability:** {df_result['trainability_category']}")
        st.markdown(f"**Demeanor:** {df_result['demeanor_category']}")
        st.markdown(f"**Energy Level:** {df_result['energy_level_category']}")
        st.markdown(f"**Shedding:** {df_result['shedding_category']}")
        st.markdown(f"**Grooming Frequency:** {df_result['grooming_frequency_category']}")
        st.markdown(f"**Average Expectancy:** {round(df_result['average_expectancy'])} years")
        st.markdown(f"**Average Height:** {round(df_result['average_height'])} cm")
        st.markdown(f"**Average Weight:** {round(df_result['average_weight'])} kg")
    
    with col2: st.empty()

    with col3:
        st.subheader("Comparison with other breeds")
        display_charts(df_result)

if __name__ == "__main__":
    print(f'Running at time: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))}')
    df = read_and_process_csv()
    main()
