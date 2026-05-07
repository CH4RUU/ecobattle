from fastapi import FastAPI
from pydantic import BaseModel
from app.brain import analyze_action

app = FastAPI(title="EcoBattle API", description="Gamified sustainability app API")

# Simple global database to track user progress
user_db = {
    "total_score": 0,
    "earth_health": 100,
    "active_challenge": None,
    "total_co2_saved": 0.0
}

def create_health_bar(health: int) -> str:
    """Returns a 10-character visual health bar."""
    bars = max(0, min(10, health // 10))
    return "|" * bars + "-" * (10 - bars)

class UserAction(BaseModel):
    action_description: str
    category: str

class SelectChallengeRequest(BaseModel):
    user_id: str
    challenge_id: str
    reward_points: int

@app.get("/state")
def get_state():
    return user_db

@app.post("/select-challenge")
def select_challenge(req: SelectChallengeRequest):
    return {
        "status": "success",
        "message": f"Challenge {req.challenge_id} accepted! Complete it to earn {req.reward_points} points."
    }

@app.post("/action")
def process_action(action: UserAction):
    print(f"Received action: {action.action_description} [Category: {action.category}]")
    
    # Analyze the action using our LLM and pass the current score
    analysis_result = analyze_action(action.action_description, user_db["total_score"])
    
    impact = analysis_result.get("impact_score", 0)
    co2 = analysis_result.get("co2_grams_saved", 0.0)
    
    user_db["total_score"] += impact
    user_db["total_co2_saved"] += co2
    
    # Update global state
    user_db["earth_health"] += impact
    
    # Cap Earth's health at 100
    if user_db["earth_health"] > 100:
        user_db["earth_health"] = 100
        
    # Prevent health from dropping below 0
    if user_db["earth_health"] < 0:
        user_db["earth_health"] = 0
    
    current_level = analysis_result.get("current_level", "Seedling")
    level_description = analysis_result.get("level_description", "Just starting out.")
    health_bar = create_health_bar(user_db["earth_health"])
    
    response = {
        "status": "received", 
        "points_impact": impact, 
        "co2_grams_saved": co2,
        "message": analysis_result.get("game_message", "Action recorded!"),
        "environmental_fact": analysis_result.get("environmental_fact", ""),
        "available_choices": analysis_result.get("available_challenges", []),
        "total_score": user_db["total_score"],
        "total_co2_saved": user_db["total_co2_saved"],
        "earth_health": user_db["earth_health"],
        "health_bar": health_bar,
        "current_level": current_level,
        "level_description": level_description,
        "game_over": False
    }
    
    if user_db["earth_health"] <= 0:
        response["game_over"] = True
        from app.brain import generate_eulogy
        response["message"] = generate_eulogy(user_db["total_score"])
        
    return response
