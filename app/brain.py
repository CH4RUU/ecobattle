import os
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from app.carbon_engine import get_co2_impact

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    max_retries=1,
    timeout=10
)

# ==========================================
# STATE DEFINITION
# ==========================================
class GameState(TypedDict, total=False):
    user_action: str
    total_score: int
    
    # Node 1 Outputs
    is_relevant: bool
    extracted_category: str
    quantity: float
    guardrail_reason: str
    
    # Node 2 Outputs
    co2_grams_saved: float
    impact_score: int
    game_status: str
    
    # Node 3 Outputs
    environmental_fact: str
    game_message: str
    available_challenges: list
    current_level: str
    level_description: str

# ==========================================
# NODE 1: Extraction Node
# ==========================================
class ExtractionOutput(BaseModel):
    is_relevant: bool = Field(description="Whether the action is related to environment/sustainability.")
    reason: str = Field(description="Explanation of relevance.")
    category: str = Field(description="The core item/action (e.g. 'plastic bottle', 'tree planted'). 'unknown' if irrelevant.")
    quantity: float = Field(description="The number of units involved (e.g. 3, 1.5). Default to 1.0 if not specified.")

extract_parser = JsonOutputParser(pydantic_object=ExtractionOutput)
extract_prompt = PromptTemplate(
    template="""Analyze the following user action: {user_input}
1. Determine if it is related to the environment.
2. Extract the core category of the action.
3. Extract the quantity.

{format_instructions}""",
    input_variables=["user_input"],
    partial_variables={"format_instructions": extract_parser.get_format_instructions()}
)
extract_chain = extract_prompt | llm | extract_parser

def extraction_node(state: GameState) -> GameState:
    action = state["user_action"]
    try:
        result = extract_chain.invoke({"user_input": action})
        return {
            "is_relevant": result.get("is_relevant", False),
            "extracted_category": result.get("category", "unknown"),
            "quantity": result.get("quantity", 1.0),
            "guardrail_reason": result.get("reason", "No reason provided.")
        }
    except Exception as e:
        print(f"Extraction error: {e}")
        # OFFLINE FALLBACK: Keep the game alive during rate limits!
        from app.carbon_engine import EMISSION_FACTORS
        import re
        action_lower = action.lower()
        extracted_cat = "unknown"
        for key in EMISSION_FACTORS.keys():
            if key in action_lower or key.split()[-1] in action_lower:
                extracted_cat = key
                break
                
        quantity = 1.0
        nums = re.findall(r'\d+', action)
        if nums:
            quantity = float(nums[0])
            
        # Basic context analysis since AI is offline
        bad_words = ["threw", "burn", "drop", "waste", "litter", "destroy", "cut"]
        if any(word in action_lower for word in bad_words):
            quantity = -abs(quantity) # Negate it so it hurts the Earth!
            
        if extracted_cat != "unknown":
            return {"is_relevant": True, "extracted_category": extracted_cat, "quantity": quantity, "guardrail_reason": "Matched via offline fallback."}
            
        return {"is_relevant": False, "extracted_category": "unknown", "quantity": 0.0, "guardrail_reason": "Google API Rate Limit exceeded. Please try again later."}

# ==========================================
# NODE 2: Data Verification Node
# ==========================================
def data_verification_node(state: GameState) -> GameState:
    if not state.get("is_relevant", False):
        return {"co2_grams_saved": 0.0, "impact_score": 0, "game_status": "Neutral impact"}
        
    category = state.get("extracted_category", "unknown")
    quantity = state.get("quantity", 1.0)
    
    # Use the Carbon Engine!
    co2_saved = get_co2_impact(category, quantity)
    
    # Mathematical conversion: 100g CO2 = 1 point
    impact_score = int(co2_saved / 100.0)
    
    if impact_score < 0:
        status = "Earth is taking damage"
    elif impact_score > 0:
        status = "Earth is thriving"
    else:
        status = "Neutral impact"
        
    return {
        "co2_grams_saved": co2_saved,
        "impact_score": impact_score,
        "game_status": status
    }

# ==========================================
# NODE 3: Generation Node (Mega-Prompt)
# ==========================================
class ChallengeOption(BaseModel):
    id: str = Field(description="'A' or 'B'")
    task: str = Field(description="The eco-challenge task description")
    reward_points: int = Field(description="Points awarded")

class GenerationOutput(BaseModel):
    game_message: str = Field(description="Witty game master comment about the action and its CO2 impact.")
    environmental_fact: str = Field(description="A fact related to the action's CO2 impact.")
    current_level: str = Field(description="Unique, thematic Level Name based on total_score.")
    level_description: str = Field(description="1-sentence description of the user's status.")
    available_challenges: list[ChallengeOption] = Field(description="Exactly two distinct eco-challenges.")

gen_parser = JsonOutputParser(pydantic_object=GenerationOutput)
gen_prompt = PromptTemplate(
    template="""You are the EcoBattle Game Master.
User Action: {user_action}
CO2 Grams Saved: {co2}
Impact Score: {impact}
Total Score: {total_score}

Based on this data, generate the full narrative response.
Include:
1. A witty message praising or scolding the user based on the CO2 impact.
2. A related environmental fact.
3. A creative Level Name and Description based on their Total Score.
4. TWO distinct eco-challenges (Choice A: The Sprint (Easy), Choice B: The Marathon (Hard)).

{format_instructions}""",
    input_variables=["user_action", "co2", "impact", "total_score"],
    partial_variables={"format_instructions": gen_parser.get_format_instructions()}
)
gen_chain = gen_prompt | llm | gen_parser

def generation_node(state: GameState) -> GameState:
    if not state.get("is_relevant", False):
        return {
            "game_message": f"Game Master says: '{state.get('guardrail_reason')}'",
            "environmental_fact": "Action not verified due to speed.",
            "current_level": "Seedling",
            "level_description": "Just starting out.",
            "available_challenges": [
                {"id": "A", "task": "Take a 5-minute nature walk.", "reward_points": 10},
                {"id": "B", "task": "Start a compost bin.", "reward_points": 100}
            ]
        }
        
    try:
        result = gen_chain.invoke({
            "user_action": state["user_action"],
            "co2": state.get("co2_grams_saved", 0),
            "impact": state.get("impact_score", 0),
            "total_score": state.get("total_score", 0)
        })
        return {
            "game_message": result.get("game_message", ""),
            "environmental_fact": result.get("environmental_fact", ""),
            "current_level": result.get("current_level", "Seedling"),
            "level_description": result.get("level_description", ""),
            "available_challenges": result.get("available_challenges", [])
        }
    except Exception as e:
        print(f"Generation error: {e}")
        
        # Offline dynamic response since AI is locked out
        co2 = state.get('co2_grams_saved', 0)
        if co2 < 0:
            msg = f"[OFFLINE MODE] You damaged the Earth! This action emitted {abs(co2):.1f}g of CO2."
        elif co2 > 0:
            msg = f"[OFFLINE MODE] Great job! You saved the Earth from {co2:.1f}g of CO2."
        else:
            msg = "[OFFLINE MODE] Neutral action recorded."
            
        return {
            "game_message": msg,
            "environmental_fact": "AI is currently offline. Upgrade API tier for dynamic facts!",
            "current_level": "Eco-Warrior (Offline)",
            "level_description": "Playing without AI assistance.",
            "available_challenges": [
                {"id": "A", "task": "Take a 5-minute nature walk.", "reward_points": 10},
                {"id": "B", "task": "Start a compost bin.", "reward_points": 100}
            ]
        }

# ==========================================
# GRAPH COMPILATION
# ==========================================
builder = StateGraph(GameState)

builder.add_node("extraction", extraction_node)
builder.add_node("data_verification", data_verification_node)
builder.add_node("generation", generation_node)

builder.add_edge(START, "extraction")
builder.add_edge("extraction", "data_verification")
builder.add_edge("data_verification", "generation")
builder.add_edge("generation", END)

game_graph = builder.compile()

def analyze_action(user_input: str, total_score: int = 0) -> dict:
    result = game_graph.invoke({
        "user_action": user_input,
        "total_score": total_score
    })
    return result

# ==========================================
# EULOGY GENERATOR
# ==========================================
eulogy_prompt = PromptTemplate(
    template="""You are the EcoBattle Game Master. The Earth's health has reached 0. 
Generate a brief, dramatic, and witty 'Final Eulogy' for the Earth based on the player's final score of {total_score}.
Make it sound like a "Game Over" screen narration.""",
    input_variables=["total_score"]
)
eulogy_chain = eulogy_prompt | llm | StrOutputParser()

def generate_eulogy(total_score: int) -> str:
    try:
        return eulogy_chain.invoke({"total_score": total_score}).strip()
    except Exception as e:
        return "The Earth has collapsed under the weight of poor choices. Game Over."
