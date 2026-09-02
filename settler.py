import os
import requests
from supabase import create_client, Client

# 1. Initialize Supabase
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def get_match_stats(match_name):
    # Insert your API-Football or Sportmonks request logic here
    # Example: Fetching the final Yellow Cards count
    # return actual_cards 
    return 6 

def settle_bets():
    print("🔍 Scanning for PENDING bets...")
    
    # 2. Fetch unsettled matches
    response = supabase.table("ev_anomalies").select("*").eq("status", "PENDING").execute()
    pending_bets = response.data
    
    if not pending_bets:
        print("✅ No pending bets to settle.")
        return

    for bet in pending_bets:
        match_name = bet['match_name']
        market = bet['market'] # Example: "OVER 4.5"
        
        # 3. Pull actual results
        actual_cards = get_match_stats(match_name)
        
        # Extract the line (e.g., 4.5)
        line = float(market.split(" ")[1])
        is_over = "OVER" in market
        
        # 4. Grade the bet
        if is_over and actual_cards > line:
            status = 'WON'
        elif not is_over and actual_cards < line:
            status = 'WON'
        else:
            status = 'LOST'
            
        # 5. Push graded status to Supabase
        supabase.table("ev_anomalies").update({"status": status}).eq("id", bet['id']).execute()
        print(f"✅ SETTLED: {match_name} | Actual Cards: {actual_cards} | Result: {status}")

if __name__ == "__main__":
    settle_bets()