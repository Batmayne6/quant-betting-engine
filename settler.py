import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file (for local testing)
load_dotenv()

# 1. Initialize Supabase securely
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("🚨 Missing Supabase credentials! Check your .env file or GitHub Secrets.")

supabase: Client = create_client(url, key)

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
        market = bet['market'] # Example: "OVER 4.5 Cards"
        
        try:
            # 3. Pull actual results (Currently mocked to always return 6)
            actual_cards = get_match_stats(match_name)
            
            # Extract the line (e.g., grabs "4.5" from "OVER 4.5 Cards")
            line = float(market.split(" ")[1])
            is_over = "OVER" in market.upper()
            
            # 4. Grade the bet
            if is_over and actual_cards > line:
                status = 'WON'
            elif not is_over and actual_cards < line:
                status = 'WON'
            else:
                status = 'LOST'
                
            # 5. Push graded status to Supabase
            supabase.table("ev_anomalies").update({"status": status}).eq("id", bet['id']).execute()
            print(f"✅ SETTLED: {match_name} | Actual: {actual_cards} | Result: {status}")
            
        except Exception as e:
            print(f"❌ ERROR settling {match_name}: {e}")

if __name__ == "__main__":
    settle_bets()