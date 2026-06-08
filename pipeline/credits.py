import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

COST_PER_RUN = 4  # 4 credits per repurposing run (1 per asset)

def get_balance(user_id: str) -> int:
    result = supabase.table("credits")\
        .select("balance")\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        # First time user — create credit record with 10 free credits
        supabase.table("credits").insert({
            "user_id": user_id,
            "balance": 10
        }).execute()
        return 10
    
    return result.data[0]["balance"]

def deduct_credits(user_id: str, amount: int, description: str) -> int:
    # 1. Get current balance    
    balance = get_balance(user_id)
    # 2. Update balance (subtract amount)    
    current_balance = balance - amount
    supabase.table("credits")\
            .update({"balance": current_balance})\
            .eq("user_id", user_id)\
            .execute()
  
    # 3. Insert a credit_transactions row (audit log)
    supabase.table("credit_transactions").insert({
    "user_id": user_id,
    "amount": -amount,  # negative = spent
    "description": description
}).execute()
    # 4. Return new balance
    return current_balance