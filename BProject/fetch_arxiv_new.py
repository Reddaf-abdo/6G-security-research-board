import requests
import pandas as pd
from datetime import datetime

# arXiv API endpoint
url = "http://export.arxiv.org/api/query"

# Search parameters
params = {
    "search_query": "6G AND security",  # Search term
    "start": 0,                         # Start index
    "max_results": 10,                  # Number of results
    "sortBy": "submittedDate",          # Sort by submission date
    "sortOrder": "descending"           # Newest first
}

# Fetch data from arXiv API
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code != 200:
    print(f"Error: Failed to fetch data (status code {response.status_code})")
    exit()

# Parse the XML response
from xml.etree import ElementTree as ET
root = ET.fromstring(response.content)

# Extract paper data
data = []
for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
    try:
        # Extract title
        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
        
        # Extract publication date
        pub_date = entry.find("{http://www.w3.org/2005/Atom}published").text
        pub_date = datetime.fromisoformat(pub_date).strftime("%Y-%m-%d")
        
        # Extract abstract
        abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
        
        # Extract URL
        url = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()
        
        # Add to data
        data.append({
            "Document": url,
            "Title": title,
            "Pub_Date": pub_date,
            "Abstract": abstract,
            "Problem": "AI-generated placeholder",
            "Solution": "AI-generated placeholder"
        })
    except Exception as e:
        print(f"Error parsing entry: {e}")
        continue  # Skip problematic entries

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("arxiv_papers_fixed.csv", index=False)
print("Saved arXiv papers to arxiv_papers_fixed.csv!")