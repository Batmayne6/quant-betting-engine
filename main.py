import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

# 1. Load local .env variables
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("🚨 Missing Supabase credentials! Check your .env file.")

supabase: Client = create_client(url, key)

def calculate_quarter_kelly(prob, decimal_odds):
    """
    Kelly Criterion Formula: f = (bp - q) / b
    b = decimal odds - 1
    p = probability of winning
    q = probability of losing (1 - p)
    """
    b = decimal_odds - 1
    q = 1 - prob
    
    if b <= 0:
        return 0
        
    kelly_fraction = (b * prob - q) / b
    quarter_k = kelly_fraction / 4
    
    # Floor at 0 to prevent negative stakes on bad edges
    return max(0, round(quarter_k, 3)) 

def scrape_sportybet_and_score():
    print("🚀 Booting Playwright engine...")
    
    # 2. Intercept Bookmaker Data
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # NOTE: In production, you will navigate to the sportsbook here
        # page.goto("https://www.sportybet.com/zm/...")
        print("📡 Intercepting JSON APIs...")
        
        # --- MOCK DATA FOR TONIGHT'S TEST ---
        # Tomorrow, we will replace this with your actual intercepted JSON response
        mock_matches = [
            {"match": "Bayern Munich vs Dortmund", "market": "OVER 4.5 Cards", "odds": 2.25},
            {"match": "Juventus vs AC Milan", "market": "UNDER 9.5 Corners", "odds": 1.95}
        ]
        
        browser.close()

    print("🧠 Scoring against XGBoost model...")
    
    # 3. Score Edges and Push to Database
    for match in mock_matches:
        # Assuming your XGBoost outputs a 55% true win probability for these specific lines
        model_prob = 0.55 
        bookie_odds = match["odds"]
        
        # Expected Value = (Probability * Decimal Odds) - 1
        ev = (model_prob * bookie_odds) - 1
        
        if ev > 0:
            print(f"✅ +EV Anomaly Found: {match['match']} | Edge: {ev*100:.1f}%")
            
            q_kelly = calculate_quarter_kelly(model_prob, bookie_odds)
            
            # 4. Fire into Supabase
            try:
                supabase.table("ev_anomalies").insert({
                    "match_date": datetime.utcnow().isoformat(),
                    "match_name": match["match"],
                    "market": match["market"],
                    "model_prob": model_prob,
                    "bookie_odds": bookie_odds,
                    "ev_edge": ev * 100,
                    "quarter_kelly": q_kelly,
                    "status": "PENDING"
                }).execute()
                print(f"💾 Saved to Supabase: {match['match']}")
            except Exception as e:
                print(f"❌ Database Error on {match['match']}: {e}")
        else:
            print(f"❌ Negative EV (-): Skipping {match['match']}")

if __name__ == "__main__":
    scrape_sportybet_and_score()