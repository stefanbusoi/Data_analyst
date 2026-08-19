import pandas as pd
import argparse

def find_duplicates(input_file, output_file, clean_file):
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Could not find file {input_file}.")
        print("Make sure you run analyse.py first to generate the summary file.")
        return

    matched_df = df[df['matched_veridion_id'].notnull()]
    unmatched_df = df[df['matched_veridion_id'].isnull()]

    duplicate_counts = matched_df['matched_veridion_id'].value_counts()
    duplicates_ids = duplicate_counts[duplicate_counts > 1].index

    if len(duplicates_ids) > 0:
        duplicates_df = matched_df[matched_df['matched_veridion_id'].isin(duplicates_ids)].copy()
        
        duplicates_df = duplicates_df.sort_values(by=['matched_veridion_id', 'match_score'], ascending=[True, False])

        print("================ DUPLICATE SUMMARY ================")
        print(f"Found {len(duplicates_ids)} unique Veridion real-world entities.")
        print(f"These correspond to {len(duplicates_df)} different entries (with possible typos/variations) in the client's initial file.")
        print("===================================================\n")
        
        duplicates_df.to_csv(output_file, index=False)
        print(f"Duplicate details have been saved to {output_file}")
    else:
        print("No duplicates were found in the client data based on the matches.")

    matched_df_sorted = matched_df.sort_values(by='match_score', ascending=False)
    
    deduplicated_matched = matched_df_sorted.drop_duplicates(subset=['matched_veridion_id'], keep='first')

    final_clean_df = pd.concat([deduplicated_matched, unmatched_df]).sort_values(by='input_row_key')
    
    final_clean_df.to_csv(clean_file, index=False)
    
    print(f"\n================ DUPLICATE ELIMINATION ================")
    print(f"The cleaned database has been saved to: {clean_file}")
    print(f"Total initial rows: {len(df)}")
    print(f"Total rows after cleaning: {len(final_clean_df)}")
    print(f"Removed {len(df) - len(final_clean_df)} duplicate entries, keeping only the best match!")
    print("=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finds duplicate entries in client data based on Veridion ID and generates a clean CSV.")
    parser.add_argument("-i", "--inputFile", help="The summary file resulting from analyse.py", default="resolved_entities_summary.csv")
    parser.add_argument("-o", "--outputFile", help="The file where ONLY the duplicates will be saved", default="client_duplicates_found.csv")
    parser.add_argument("-c", "--cleanFile", help="The DEDUPLICATED file, containing the cleaned database", default="resolved_entities_deduplicated.csv")
    
    args = parser.parse_args()
    find_duplicates(args.inputFile, args.outputFile, args.cleanFile)
