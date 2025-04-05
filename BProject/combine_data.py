import pandas as pd

# Load real papers
real_df = pd.read_csv("real_papers.csv")

# Load fake patents
fake_df = pd.read_csv("fake_patents.csv")

# Combine the two datasets
combined_df = pd.concat([real_df, fake_df])

# Save the final dataset
combined_df.to_csv("final_data.csv", index=False)
print("Combined data saved to final_data.csv!")