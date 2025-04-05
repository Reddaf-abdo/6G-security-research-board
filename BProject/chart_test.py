import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="6G Security Research", page_icon="🚀", layout="wide",
                    initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .st-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-bottom: 1px solid #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("final_data_processed be bacl.csv", delimiter=";")

    def parse_date(date_str):
        if isinstance(date_str, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y",
                        "%Y/%m/%d"):  # Add more formats if needed
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    pass  # Try the next format
        return None  # Return None for invalid dates

    df['Pub_Date_Parsed'] = df['Pub_Date'].apply(parse_date)
    df.dropna(subset=['Pub_Date_Parsed'], inplace=True)  # Drop rows where date parsing failed
    df['Pub_Date_Parsed'] = pd.to_datetime(df['Pub_Date_Parsed'])  # Ensure datetime format

    return df

df = load_data()

# --- App Layout ---
st.markdown("<h1 style='text-align: center; color: #007bff;'>6G Security Research Dashboard</h1>",
            unsafe_allow_html=True)

# --- Key Metrics ---
st.markdown("<h2 style='color: #4caf50;'>Key Metrics</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total Documents", len(df))
col2.metric("Latest Publication",
            df['Pub_Date_Parsed'].max().strftime('%Y-%m-%d') if not df['Pub_Date_Parsed'].empty else "N/A")
col3.metric("Number of Patents", len(df[df['Document'].str.contains("patents.google.com")]))

# --- Sidebar Filters ---
st.sidebar.header("Filters")
st.sidebar.subheader("Filter Documents")
keyword = st.sidebar.text_input("Keyword Search", "")

start_date = pd.to_datetime(st.sidebar.date_input("Start Date", value=datetime(2023, 1, 1).date()))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", value=datetime.now().date()))

source_filter = st.sidebar.selectbox("Source", ["All", "arXiv", "Patents"])
if 'Topic' in df.columns:
    topic_filter = st.sidebar.selectbox("Filter by Topic", options=["All"] + list(df['Topic'].unique()))
else:
    topic_filter = "All"

# --- Filter Data ---
filtered_df = df[
    (df['Title'].str.contains(keyword, case=False) | df['Abstract'].str.contains(keyword, case=False)) &
    (df['Pub_Date_Parsed'] >= start_date) & (filtered_df['Pub_Date_Parsed'] <= end_date)
].copy()

if source_filter != "All":
    if source_filter == "arXiv":
        filtered_df = filtered_df[filtered_df['Document'].str.contains("arxiv.org")]
    elif source_filter == "Patents":
        filtered_df = filtered_df[filtered_df['Document'].str.contains("patents.google.com")]

if 'Topic' in df.columns and topic_filter != "All":
    filtered_df = filtered_df[filtered_df['Topic'] == topic_filter]

# --- Source Display ---
def display_source(document_link):
    if "arxiv.org" in document_link:
        return "📄 arXiv Paper"
    elif "patents.google.com" in document_link:
        return " patent"
    else:
        return "🔗 Document"

filtered_df['Source'] = filtered_df['Document'].apply(display_source)

# --- Make Links Clickable ---
def make_clickable(url):
    return f'<a href="{url}" target="_blank">{url}</a>'

filtered_df['Document'] = filtered_df['Document'].apply(make_clickable)

st.header("Research Documents")

# --- Charts ---
st.subheader("Data Visualizations")

# 1. Publications Over Time (Bar Chart)
if not filtered_df.empty:  # Check if DataFrame is not empty
    publications_by_year = filtered_df.groupby(filtered_df['Pub_Date_Parsed'].dt.year).size()
    st.bar_chart(publications_by_year)
    st.caption("Number of Publications per Year")
else:
    st.write("No data to display charts.")

# 2. Source Distribution (Bar Chart) - Replaced Pie Chart
source_counts = filtered_df['Source'].value_counts()
st.bar_chart(source_counts)  # Using a simple bar chart
st.caption("Document Source Distribution")

# 3. Keyword Counts (Bar Chart - Top 10)
def extract_keywords(text):
    if isinstance(text, str):
        return text.split(',')  # Simple split, improve as needed
    else:
        return []

if 'Keywords' in df.columns:  # Only if you have a Keywords column
    df['Keywords_List'] = df['Keywords'].apply(extract_keywords)
    all_keywords = [word.strip() for sublist in df['Keywords_List'] for word in sublist]
    keyword_counts = pd.Series(all_keywords).value_counts().head(10)
    st.bar_chart(keyword_counts)
    st.caption("Top 10 Keywords")

# --- Display Results ---
st.subheader("Filtered Documents")
st.write(filtered_df[['Source', 'Title', 'Pub_Date', 'Problem', 'Solution']].to_html(escape=False),
         unsafe_allow_html=True)

# --- Expandable Abstracts ---
with st.expander("Show Document Abstracts"):
    for index, row in filtered_df.iterrows():
        st.write(f"**{row['Title']}**")
        st.write(row['Abstract'])
        st.markdown("---")

# --- Download Button ---
file_name = f"6g_security_results_{datetime.now().strftime('%Y%m%d')}.csv"
st.download_button(
    label="Download Filtered Data",
    data=filtered_df.to_csv(index=False, sep=";").encode('utf-8'),
    file_name=file_name,
    mime="text/csv"
)

st.sidebar.markdown("---")

# --- System Health ---
st.sidebar.header("System Health")
st.sidebar.progress(95, text="Data Acquisition: Operational")
st.sidebar.progress(90, text="AI Analysis: Stable")
st.sidebar.progress(80, text="Interface: Operational")