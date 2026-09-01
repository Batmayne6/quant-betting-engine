import os
from supabase import create_client, Client

# 1. Fetch the secrets securely from Render's environment
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Safety check to ensure the keys loaded correctly
if not url or not key:
    raise ValueError("🚨 Missing Supabase credentials! Check your Render environment variables.")

# 2. Initialize the Supabase client
supabase: Client = create_client(url, key)

def push_bet_to_database(match_name, market, model_prob, bookie_odds, edge, stake):
    """
    Pushes a found +EV anomaly to the Supabase database.
    """
    data = {
        "match_name": match_name,
        "market": market,
        "model_prob": model_prob,
        "bookie_odds": bookie_odds,
        "ev_edge": edge,
        "quarter_kelly": stake,
        "status": "PENDING"
    }
    
    # Insert the data into the 'ev_anomalies' table
    response = supabase.table("ev_anomalies").insert(data).execute()
    print(f"✅ Logged to Supabase: {match_name}")
    return response