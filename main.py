import os
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

# 1. Load local .env variables
load_dotenv(".env.local")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("🚨 Missing Supabase credentials! Check your .env file.")

supabase: Client = create_client(url, key)

def calculate_quarter_kelly(prob, decimal_odds):
    b = decimal_odds - 1
    q = 1 - prob
    if b <= 0:
        return 0
    return max(0, round(((b * prob - q) / b) / 4, 3)) 

def scrape_sportybet_and_score():
    print("🚀 Booting Playwright engine for Live Extraction...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("🌐 Navigating to SportyBet Zambia...")
        
        try:
            # 2. Intercept the Live Football API
            with page.expect_response(lambda response: "factsCenter/importantEvents" in response.url and "sportId=sr%3Asport%3A1" in response.url, timeout=15000) as response_info:
                page.goto("https://www.sportybet.com/zm/", wait_until="domcontentloaded")
            
            print("🎯 Live odds intercepted! Parsing JSON...")
            odds_data = response_info.value.json()
            
            matches_extracted = []
            
            # 3. Unpack SportyBet's JSON format
            for tournament in odds_data.get("data", []):
                for event in tournament.get("events", []):
                    match_name = f"{event.get('homeTeamName')} vs {event.get('awayTeamName')}"
                    
                    for market in event.get("markets", []):
                        market_group = market.get("desc")
                        specifier = market.get("specifier", "")
                        
                        # Clean up market names (e.g., turn "Over/Under total=2.5" into "Over/Under 2.5")
                        if "total=" in specifier:
                            market_group = f"{market_group} {specifier.split('=')[1]}"
                            
                        for outcome in market.get("outcomes", []):
                            selection = outcome.get("desc")
                            odds = float(outcome.get("odds", 0))
                            
                            if odds > 1.10: # Filter out ultra-low odds
                                matches_extracted.append({
                                    "match": match_name,
                                    "market": f"{market_group} - {selection}",
                                    "odds": odds
                                })

            print(f"✅ Extracted {len(matches_extracted)} total betting lines. Scoring against model...")
            
            # 4. Score against Real XGBoost Model and Push Anomalies
            for match in matches_extracted:
                bookie_odds = match["odds"]
                
                # ---> YOUR XGBOOST INFERENCE HERE <---
                # 1. Extract the features for match['match'] (e.g., xG, Poisson stats)
                # 2. Pass them to your model: 
                # model_prob = my_xgb_model.predict(features)[0]
                
                # (Temporary placeholder until you paste your real model logic)
                model_prob = (1 / bookie_odds) + 0.05 
                
                ev = (model_prob * bookie_odds) - 1
                
                if ev > 0.03: # Only trigger on edges greater than 3%
                    q_kelly = calculate_quarter_kelly(model_prob, bookie_odds)
                    
                    try:
                        supabase.table("ev_anomalies").insert({
                            "match_date": datetime.now(timezone.utc).isoformat(),
                            "match_name": match["match"],
                            "market": match["market"],
                            "model_prob": round(model_prob, 3),
                            "bookie_odds": bookie_odds,
                            "ev_edge": round(ev * 100, 2),
                            "quarter_kelly": q_kelly,
                            "status": "PENDING"
                        }).execute()
                        print(f"💰 EDGE FOUND: {match['match']} | Market: {match['market']} | EV: {ev*100:.1f}%")
                    except Exception as e:
                        print(f"❌ Database Error: {e}")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            
        finally:
            browser.close()

    print("🛑 Live engine cycle complete.")

if __name__ == "__main__":
    scrape_sportybet_and_score()