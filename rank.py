import argparse
import json
import gzip
import csv
import sys
import os

# Import our helper functions from utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import is_honeypot, is_pure_consulting, calculate_score, generate_reasoning

def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Path to output submission CSV")
    args = parser.parse_args()
    
    # Check if candidates file is gzipped
    is_gzip = args.candidates.endswith(".gz")
    
    candidates_scored = []
    
    print("Reading and scoring candidates...")
    open_func = gzip.open if is_gzip else open
    mode = "rt" if is_gzip else "r"
    
    count = 0
    filtered_honeypot = 0
    filtered_consulting = 0
    
    with open_func(args.candidates, mode, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            count += 1
            if count % 20000 == 0:
                print(f"Processed {count} candidates...")
                
            candidate = json.loads(line)
            cid = candidate["candidate_id"]
            
            # Filter 1: Honeypots/Trap profiles
            if is_honeypot(candidate):
                filtered_honeypot += 1
                continue
                
            # Filter 2: Pure consulting/services candidates
            if is_pure_consulting(candidate):
                filtered_consulting += 1
                continue
                
            # Calculate final fit score
            score = calculate_score(candidate)
            candidates_scored.append({
                "candidate_id": cid,
                "score": score,
                "candidate": candidate
            })
            
    print(f"Total candidates scanned: {count}")
    print(f"Filtered honeypots: {filtered_honeypot}")
    print(f"Filtered pure consulting: {filtered_consulting}")
    print(f"Scored candidate pool: {len(candidates_scored)}")
    
    # Sort: primarily by score descending, secondarily by candidate_id ascending (lexicographical tie-breaker)
    candidates_scored.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Select top 100
    top_100 = candidates_scored[:100]
    
    # Write to CSV in the required format
    print(f"Writing top 100 to {args.out}...")
    with open(args.out, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank_idx, item in enumerate(top_100):
            rank = rank_idx + 1
            cid = item["candidate_id"]
            score = item["score"]
            cand = item["candidate"]
            
            # Generate specific, factual reasoning
            reasoning = generate_reasoning(cand, rank)
            
            writer.writerow([cid, rank, score, reasoning])
            
    print("Ranking successfully completed.")

if __name__ == "__main__":
    main()
