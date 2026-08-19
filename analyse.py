import pandas as pd
from rapidfuzz import fuzz
import sys
import re
import argparse

parser = argparse.ArgumentParser()

defaultScoreTreshold=70.0
defaultInputFile="presales_data_sample.csv"
defaultOutputFile="resolved_entities_summary.csv"

parser.add_argument("-s","--scoreThreshold", help=f"Threshold for matching (between 0-100) (default: {defaultScoreTreshold})",type=float,default=defaultScoreTreshold)
parser.add_argument("-i","--inputFile", help=f"Input file name (default: {defaultInputFile})",type=str,default=defaultInputFile)
parser.add_argument("-o","--outputFile", help=f"Output file name (default: {defaultOutputFile})",type=str,default=defaultOutputFile)
parser.add_argument("-u","--unresolvedFile", help="Output file name for unresolved entities (default: None)",type=str,default=None)

args = parser.parse_args()
scoreThreshold = args.scoreThreshold

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


def clean_str(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s.lower()

def clean_company_name(name):
    name = clean_str(name)
    if not name:
        return ""
    
    cleaned = re.sub(r'[^\w\s]', ' ', name)
    
    suffixes = {
        'inc', 'llc', 'ltd', 'gmbh', 'corp', 'corporation', 'co', 'srl', 'sa', 'plc', 
        'aps', 'ab', 'as', 'oy', 'pte', 'sdn', 'bhd', 'pvt', 'private', 'limited', 
        'spa', 'nv', 'bv', 'ag', 'kg'
    }
    
    words = [w for w in cleaned.split() if w not in suffixes]
    
    return " ".join(words)

def calculate_validity_score(row):
    validity_score = 100
    email = str(row.get('primary_email', '')).lower()
    common_domains = ['@gmail.', '@yahoo.', '@hotmail.', '@outlook.', '@aol.', '@icloud.', '@live.', '@msn.']
    if any(domain in email for domain in common_domains):
        validity_score = 90
    return validity_score

def calculate_match_score(row):
    input_name = clean_company_name(row['input_company_name'])
    
    candidate_names = [clean_company_name(row['company_name'])]
    
    if not pd.isna(row.get('company_legal_names')):
        legal_names = str(row['company_legal_names']).split('|')
        candidate_names.extend([clean_company_name(n) for n in legal_names])
        
    if not pd.isna(row.get('company_commercial_names')):
        comm_names = str(row['company_commercial_names']).split('|')
        candidate_names.extend([clean_company_name(n) for n in comm_names])
        
    name_score = max([fuzz.token_sort_ratio(input_name, c_name) for c_name in candidate_names if c_name] + [0])
    
    input_country = clean_str(row.get('input_main_country_code', ''))
    candidate_country = clean_str(row.get('main_country_code', ''))
    
    country_score = 0
    if input_country:
        if input_country == candidate_country:
            country_score = 100
        else:
            locations = clean_str(row.get('locations', '')).split('|')
            for location in locations: 
                loc_tokens = location.replace(',', ' ').split()
                if input_country in loc_tokens:
                    country_score = 100
        if country_score == 0 and len(locations)<row.get('num_locations'):
            country_score=50
    
    input_city = clean_str(row.get('input_main_city', ''))
    candidate_city = clean_str(row.get('main_city', ''))
    city_score = fuzz.ratio(input_city, candidate_city) if (input_city and candidate_city) else 0
    
    input_postcode = clean_str(row.get('input_main_postcode', ''))
    candidate_postcode = clean_str(row.get('main_postcode', ''))
    postcode_score = 100 if (input_postcode and input_postcode == candidate_postcode) else 0
    
    input_street = clean_str(row.get('input_main_street', ''))
    candidate_street = clean_str(row.get('main_street', ''))
    street_score = fuzz.token_set_ratio(input_street, candidate_street) if (input_street and candidate_street) else 0
    
    if  input_street == "" and input_postcode=='':
        location_detail_score=100
    else:
        location_detail_score = max(postcode_score, street_score)
    
    if input_city == '':
        city_score=100
    if input_country == '':
        country_score=100


    total_score = (name_score * 0.45) + (country_score * 0.25) + (city_score * 0.15) + (location_detail_score * 0.15)
    if country_score == 0 and input_country != "":
        total_score *= 0.5

    validity_score = calculate_validity_score(row)
    total_score *= (validity_score / 100.0)

    return pd.Series({
        'match_score': round(total_score, 2),
        'name_score': round(name_score, 2),
        'country_score': round(country_score, 2),
        'city_score': round(city_score, 2),
        'location_detail_score': round(location_detail_score, 2),
        'validity_score': round(validity_score, 2)
    })

def main():
    file_path = args.inputFile
    
    try:
        df = pd.read_csv(file_path)
        
        resolved_results = []
        unmatched_count = 0
        high_confidence_matches = 0
        unresolved_keys = []
        
        for row_key, group in df.groupby('input_row_key'):
            group = group.copy()
            
            scores_df = group.apply(calculate_match_score, axis=1)
            group = pd.concat([group, scores_df], axis=1)
            
            sorted_group = group.sort_values(by='match_score', ascending=False)
            best_match = sorted_group.iloc[0]
            
            
            input_company = group['input_company_name'].iloc[0]
            
            if best_match['match_score'] >= scoreThreshold:
                high_confidence_matches += 1
                status = "MATCHED"
            else:
                unmatched_count += 1
                status = "UNMATCHED (Low Confidence)"
                unresolved_keys.append(row_key)
                
            print(f"Key: {row_key} | Input: {input_company}")
            print(f"  Best Match Status: {status}")
            
            for _, candidate in sorted_group.iterrows():
                candidate_id = candidate.get('veridion_id', 'N/A')
                score = candidate['match_score']
                name_score = candidate['name_score']
                country_score = candidate['country_score']
                city_score = candidate['city_score']
                location_detail_score = candidate['location_detail_score']
                validity_score = candidate.get('validity_score', 100)
                color = GREEN if score >= scoreThreshold else RED
                print(f"  {color}Candidate: {candidate_id}({candidate.get('company_name')}) | Score: {score}%| NameScore: {name_score}%| CountryScore: {country_score}%| CityScore: {city_score}%| LocationDetailScore: {location_detail_score}%| ValidityScore: {validity_score}%{RESET}")
                
            print("-" * 60)
            
            resolved_results.append({
                'input_row_key': row_key,
                'input_company_name': input_company,
                'matched_veridion_id': best_match.get('veridion_id') if best_match['match_score'] >= scoreThreshold else None,
                'match_score': best_match['match_score'],
                'status': status
            })

        print(f"\n================ SUMMARY ================")
        print(f"Total Unique Inputs: {len(resolved_results)}")
        print(f"{GREEN}Successfully Matched (Score >= {scoreThreshold}%): {high_confidence_matches}{RESET}")
        print(f"{RED}Unmatched / Manual Review Needed: {unmatched_count}{RESET}")
        print(f"==========================================\n")
        
        results_df = pd.DataFrame(resolved_results)
        results_df.to_csv(args.outputFile, index=False)
        print(f"Results have been saved to {args.outputFile}")
        
        if args.unresolvedFile and unresolved_keys:
            unresolved_df = df[df['input_row_key'].isin(unresolved_keys)]
            unresolved_df.to_csv(args.unresolvedFile, index=False)
            print(f"Unresolved entities have been saved to {args.unresolvedFile}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
