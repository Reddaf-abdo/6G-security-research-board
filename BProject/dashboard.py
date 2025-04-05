import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit.components.v1 import html
import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

st.set_page_config(page_title="6G Security Research", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .st-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-bottom: 1px solid #ccc;
    }
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("final_data_processed be bacl.csv", delimiter=";")

df = load_data()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None

df['Pub_Date_Parsed'] = df['Pub_Date'].apply(parse_date)
df = df.dropna(subset=['Pub_Date_Parsed'])

df['Year'] = df['Pub_Date_Parsed'].apply(lambda x: x.year)
df['Month'] = df['Pub_Date_Parsed'].apply(lambda x: x.month)
df['YearMonth'] = df['Pub_Date_Parsed'].apply(lambda x: x.strftime('%Y-%m'))

st.markdown("<h1 style='text-align: center; color: #007bff;'>6G Security Research Dashboard</h1>", unsafe_allow_html=True)

st.sidebar.header("Filters")
st.sidebar.subheader("Filter Documents")

keyword = st.sidebar.text_input("Keyword Search", "")
search_type = st.sidebar.radio("Search Type", ["OR", "AND"])

doc_types = ["All Types"]
if any("arxiv.org" in str(doc) for doc in df['Document']):
    doc_types.append("arXiv Papers")
if any("patents.google.com" in str(doc) for doc in df['Document']):
    doc_types.append("Patents")
doc_type = st.sidebar.selectbox("Document Type", doc_types)

start_date = st.sidebar.date_input("Start Date", value=datetime(2020, 1, 1).date())
end_date = st.sidebar.date_input("End Date", value=datetime.now().date())

if 'Problem' in df.columns:
    problems = ["All"] + sorted(list(df['Problem'].dropna().unique()))
    selected_problem = st.sidebar.selectbox("Filter by Problem Area", problems)

filtered_df = df.copy()

filtered_df = filtered_df[
    (filtered_df['Pub_Date_Parsed'] >= start_date) & (filtered_df['Pub_Date_Parsed'] <= end_date)
]

if keyword:
    keywords = [k.strip() for k in keyword.split(",")]
    if search_type == "OR":
        keyword_filter = filtered_df['Title'].str.contains(keywords[0], case=False, na=False) | filtered_df['Abstract'].str.contains(keywords[0], case=False, na=False)
        for k in keywords[1:]:
            keyword_filter = keyword_filter | filtered_df['Title'].str.contains(k, case=False, na=False) | filtered_df['Abstract'].str.contains(k, case=False, na=False)
    else:
        keyword_filter = filtered_df['Title'].str.contains(keywords[0], case=False, na=False) | filtered_df['Abstract'].str.contains(keywords[0], case=False, na=False)
        for k in keywords[1:]:
            keyword_filter = keyword_filter & (filtered_df['Title'].str.contains(k, case=False, na=False) | filtered_df['Abstract'].str.contains(k, case=False, na=False))
    filtered_df = filtered_df[keyword_filter]

if doc_type == "arXiv Papers":
    filtered_df = filtered_df[filtered_df['Document'].str.contains("arxiv.org", na=False)]
elif doc_type == "Patents":
    filtered_df = filtered_df[filtered_df['Document'].str.contains("patents.google.com", na=False)]

if 'Problem' in df.columns and selected_problem != "All":
    filtered_df = filtered_df[filtered_df['Problem'] == selected_problem]

def display_source(document_link):
    if isinstance(document_link, str):
        if "arxiv.org" in document_link:
            return "📄 arXiv Paper"
        elif "patents.google.com" in document_link:
            return "📋 Patent"
    return "🔗 Document"

filtered_df['Source'] = filtered_df['Document'].apply(display_source)

def make_clickable(url):
    if isinstance(url, str):
        return f'<a href="{url}" target="_blank">{url}</a>'
    return ""

filtered_df['Document'] = filtered_df['Document'].apply(make_clickable)

st.markdown("<h2 style='color: #4caf50;'>Key Metrics</h2>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

total_docs = len(filtered_df)
total_docs_prev_period = len(df[(df['Pub_Date_Parsed'] >= start_date - pd.Timedelta(days=365)) & 
                                (df['Pub_Date_Parsed'] < start_date)])
doc_delta = total_docs - total_docs_prev_period

col1.metric("Total Documents", total_docs, delta=doc_delta, delta_color="normal")

if not filtered_df.empty:
    latest_pub = filtered_df['Pub_Date_Parsed'].max()
    sorted_dates = sorted(filtered_df['Pub_Date_Parsed'].unique())
    if len(sorted_dates) > 1:
        prev_pub = sorted_dates[-2]
        days_delta = (latest_pub - prev_pub).days
        col2.metric("Latest Publication", latest_pub.strftime("%d/%m/%Y"), delta=f"{days_delta} days", delta_color="off")
    else:
        col2.metric("Latest Publication", latest_pub.strftime("%d/%m/%Y"))
else:
    col2.metric("Latest Publication", "No data")

patents_count = len(filtered_df[filtered_df['Document'].str.contains("patents.google.com", na=False)])
patents_count_prev = len(df[(df['Document'].str.contains("patents.google.com", na=False)) & 
                               (df['Pub_Date_Parsed'] >= start_date - pd.Timedelta(days=365)) & 
                               (df['Pub_Date_Parsed'] < start_date)])
patents_delta = patents_count - patents_count_prev
col3.metric("Number of Patents", patents_count, delta=patents_delta)

papers_count = len(filtered_df[filtered_df['Document'].str.contains("arxiv.org", na=False)])
papers_count_prev = len(df[(df['Document'].str.contains("arxiv.org", na=False)) & 
                              (df['Pub_Date_Parsed'] >= start_date - pd.Timedelta(days=365)) & 
                              (df['Pub_Date_Parsed'] < start_date)])
papers_delta = papers_count - papers_count_prev
col4.metric("Number of Papers", papers_count, delta=papers_delta)

if filtered_df.empty:
    st.warning("No documents match your filter criteria. Please adjust your filters.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Visualization", "📑 Research Documents", "🔍 Text Analysis", "📈 Trend Analysis"])

    with tab1:
        st.header("Data Visualization")
        
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            st.subheader("Publication Timeline")
            
            timeline_data = filtered_df.groupby('YearMonth').size().reset_index(name='Count')
            timeline_data['YearMonth'] = pd.to_datetime(timeline_data['YearMonth'])
            
            fig_timeline = px.line(timeline_data, x='YearMonth', y='Count', 
                                    title='Publication Frequency Over Time',
                                    labels={'YearMonth': 'Date', 'Count': 'Number of Publications'})
            
            fig_timeline.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with viz_col2:
            st.subheader("Document Type Distribution")
            
            doc_types = filtered_df['Source'].value_counts().reset_index()
            doc_types.columns = ['Type', 'Count']
            
            fig_pie = px.pie(doc_types, values='Count', names='Type', hole=0.4,
                                title='Distribution of Document Types')
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        if 'Problem' in filtered_df.columns and 'Solution' in filtered_df.columns:
            st.subheader("Problem-Solution Relationship")
            
            try:
                top_problems = filtered_df['Problem'].value_counts().nlargest(10).index.tolist()
                top_solutions = filtered_df['Solution'].value_counts().nlargest(10).index.tolist()
                
                if top_problems and top_solutions:
                    problem_solution_df = filtered_df.dropna(subset=['Problem', 'Solution'])
                    problem_solution_df = problem_solution_df[
                        problem_solution_df['Problem'].isin(top_problems) & 
                        problem_solution_df['Solution'].isin(top_solutions)
                    ]
                    
                    if not problem_solution_df.empty:
                        problem_solution_counts = problem_solution_df.groupby(['Problem', 'Solution']).size().reset_index(name='Count')
                        
                        heatmap_data = problem_solution_counts.pivot(index='Problem', columns='Solution', values='Count').fillna(0)
                        
                        fig_heatmap = px.imshow(heatmap_data, 
                                                labels=dict(x="Solution Approach", y="Problem Area", color="Count"),
                                                title="Relationship Between Problem Areas and Solution Approaches")
                        
                        fig_heatmap.update_layout(height=500)
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                    else:
                        st.info("Not enough data to generate Problem-Solution heatmap.")
                else:
                    st.info("Not enough Problem or Solution data to generate heatmap.")
            except Exception as e:
                st.error(f"Error generating problem-solution heatmap: {e}")

    with tab2:
        st.header("Research Documents")
        
        sort_col, sort_order = st.columns(2)
        sort_by = sort_col.selectbox("Sort by", ["Pub_Date_Parsed", "Title"])
        ascending = sort_order.checkbox("Ascending order", value=False)
        
        try:
            sorted_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        except Exception:
            st.warning(f"Could not sort by {sort_by}. Using default sort.")
            sorted_df = filtered_df
        
        st.write(f"Showing {len(sorted_df)} documents:")
        
        display_cols = ['Source', 'Title', 'Pub_Date']
        for col in ['Problem', 'Solution']:
            if col in sorted_df.columns:
                display_cols.append(col)
        
        st.write(sorted_df[display_cols].to_html(escape=False), unsafe_allow_html=True)
        
        if 'Abstract' in sorted_df.columns:
            with st.expander("Show Document Abstracts"):
                for index, row in sorted_df.iterrows():
                    st.markdown(f"**{row['Title']}**")
                    st.markdown(f"*Published on: {row['Pub_Date']}*")
                    if isinstance(row.get('Abstract'), str):
                        st.write(row['Abstract'])
                    st.markdown("---")

        file_name = f"6g_security_results_{datetime.now().strftime('%Y%m%d')}.csv"
        st.download_button(
            label="Download Filtered Data",
            data=sorted_df.to_csv(index=False, sep=";").encode('utf-8'),
            file_name=file_name,
            mime="text/csv"
        )

    with tab3:
        st.header("Text Analysis")
        
        if 'Abstract' in filtered_df.columns:
            col_wordcloud, col_terms = st.columns(2)
            
            with col_wordcloud:
                st.subheader("Word Cloud")
                
                if not filtered_df.empty:
                    all_text = " ".join(filtered_df['Abstract'].dropna().astype(str))
                    
                    if all_text.strip():
                        stop_words = set(stopwords.words('english'))
                        additional_stops = {'6g', '6G', 'security', 'research', 'study', 'paper', 'also', 'however', 'thus', 'may', 'use'}
                        stop_words.update(additional_stops)
                        
                        wordcloud = WordCloud(
                            width=800, height=400,
                            background_color='white',
                            stopwords=stop_words,
                            max_words=100,
                            colormap='viridis'
                        ).generate(all_text)
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    else:
                        st.info("No abstract text available for word cloud generation.")
                else:
                    st.write("No data available to generate word cloud.")
            
            with col_terms:
                st.subheader("Top Terms")
                
                if not filtered_df.empty:
                    all_text = " ".join(filtered_df['Abstract'].dropna().astype(str)).lower()
                    
                    if all_text.strip():
                        words = all_text.split()
                        stop_words = set(stopwords.words('english'))
                        additional_stops = {'6g', '6g,', '6g.', 'security', 'research', 'study', 'paper', 'also', 'however', 'thus', 'may', 'use'}
                        stop_words.update(additional_stops)
                        
                        filtered_words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 2]
                        
                        if filtered_words:
                            word_freq = Counter(filtered_words)
                            most_common = word_freq.most_common(15)
                            
                            terms_df = pd.DataFrame(most_common, columns=['Term', 'Frequency'])
                            
                            fig_terms = px.bar(terms_df, x='Frequency', y='Term', orientation='h',
                                                title='Most Frequent Terms in Abstracts',
                                                labels={'Frequency': 'Occurrence Count', 'Term': 'Term'},
                                                color='Frequency', color_continuous_scale=px.colors.sequential.Viridis)
                            
                            fig_terms.update_layout(yaxis={'categoryorder': 'total ascending'})
                            st.plotly_chart(fig_terms, use_container_width=True)
                        else:
                            st.info("No significant terms found after filtering.")
                    else:
                        st.info("No abstract text available for term analysis.")
                else:
                    st.write("No data available to extract terms.")
        else:
            st.info("Abstract column not found in the data. Text analysis is not available.")

    with tab4:
        st.header("Trend Analysis")
        
        trend_col1, trend_col2 = st.columns(2)
        
        with trend_col1:
            st.subheader("Annual Publication Trends")
            
            annual_counts = filtered_df.groupby('Year').size().reset_index(name='Count')
            
            fig_annual = px.bar(annual_counts, x='Year', y='Count',
                                    title='Publications by Year',
                                    labels={'Year': 'Year', 'Count': 'Number of Publications'})
            
            st.plotly_chart(fig_annual, use_container_width=True)
        
        with trend_col2:
            st.subheader("Monthly Publication Patterns")
            
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
            
            monthly_counts = filtered_df.groupby('Month').size().reset_index(name='Count')
            monthly_counts['Month_Name'] = monthly_counts['Month'].map(month_names)
            monthly_counts = monthly_counts.sort_values('Month')
            
            fig_monthly = px.line(monthly_counts, x='Month_Name', y='Count',
                                    markers=True,
                                    title='Publication Distribution by Month',
                                    labels={'Month_Name': 'Month', 'Count': 'Number of Publications'})
            
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        if 'Problem' in filtered_df.columns:
            st.subheader("Problem Area Trends Over Time")
            
            try:
                problem_counts = filtered_df['Problem'].value_counts()
                if not problem_counts.empty:
                    top_problems = problem_counts.nlargest(min(5, len(problem_counts))).index.tolist()
                    
                    problem_trends = filtered_df[filtered_df['Problem'].isin(top_problems)]
                    
                    if not problem_trends.empty:
                        problem_trends = problem_trends.groupby(['Year', 'Problem']).size().reset_index(name='Count')
                        
                        fig_problem_trends = px.line(problem_trends, x='Year', y='Count', color='Problem',
                                                        markers=True,
                                                        title='Evolution of Top Problem Areas Over Time',
                                                        labels={'Year': 'Year', 'Count': 'Number of Publications', 'Problem': 'Problem Area'})
                        
                        st.plotly_chart(fig_problem_trends, use_container_width=True)
                    else:
                        st.info("Not enough data to show problem area trends.")
                else:
                    st.info("No problem areas found for trend analysis.")
            except Exception as e:
                st.error(f"Error generating problem area trends: {e}")

if 'Author_Institution_Country' in df.columns and not filtered_df.empty:
    st.header("Geographic Distribution")
    
    if filtered_df['Author_Institution_Country'].notna().any():
        country_counts = filtered_df.groupby('Author_Institution_Country').size().reset_index(name='Count')
        
        fig_map = px.choropleth(country_counts, 
                                locations='Author_Institution_Country',
                                locationmode='country names',
                                color='Count',
                                hover_name='Author_Institution_Country',
                                color_continuous_scale=px.colors.sequential.Plasma,
                                title='Research Distribution by Country')
        
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No valid country data available for geographic distribution.")

st.sidebar.markdown("---")
st.sidebar.header("System Health")
st.sidebar.progress(95, text="Data Acquisition: Operational")
st.sidebar.progress(90, text="AI Analysis: Stable")
st.sidebar.progress(80, text="Interface: Operational")

st.sidebar.markdown("---")
st.sidebar.header("Feedback")
feedback = st.sidebar.slider("How would you rate this dashboard?", 1, 5, 3)
feedback_text = st.sidebar.text_area("Any suggestions for improvement?")
if st.sidebar.button("Submit Feedback"):
    st.sidebar.success("Thank you for your feedback!")
