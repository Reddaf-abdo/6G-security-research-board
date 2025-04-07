import requests
import pandas as pd
import time

API_URL = "https://api-inference.huggingface.co/models/gpt2"  # Replace with a better model if needed
headers = {"Authorization": "Bearer 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"}  # Replace with your key

def generate_analysis(abstract):
    try:
        payload = {"inputs": f"Identify ONE key problem and solution from this 6G research abstract: {abstract}"}
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"API Error: Status code {response.status_code}")
            return "Error", "Error"
        
        result = response.json()
        if not result or 'generated_text' not in result[0]:
            print("API Error: Invalid response format")
            return "Error", "Error"
        
        generated_text = result[0]['generated_text']
        problem = generated_text.split("Problem: ")[1].split("\n")[0].strip()
        solution = generated_text.split("Solution: ")[1].strip()
        return problem, solution
    except Exception as e:
        print(f"API Error: {e}")
        return "Error", "Error"

df = pd.read_csv("final_data.csv", encoding='latin1', on_bad_lines='skip')

if 'Problem' not in df.columns:
    df['Problem'] = "AI-generated placeholder"
if 'Solution' not in df.columns:
    df['Solution'] = "AI-generated placeholder"

for index, row in df.iterrows():
    if "arxiv.org" in str(row["Document"]):  # Only process arXiv papers
        abstract = str(row["Abstract"])
        problem, solution = generate_analysis(abstract)
        df.at[index, "Problem"] = problem
        df.at[index, "Solution"] = solution
        time.sleep(5)  # Avoid rate limits (adjust as needed)

df.to_csv("final_data_processed.csv", index=False)
print("Done! Check final_data_processed.csv!")
