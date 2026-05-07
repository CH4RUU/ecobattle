from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

# Hardcoded Emission Factors (grams of CO2 per unit)
# Positive means CO2 saved, negative means CO2 emitted.
EMISSION_FACTORS = {
    "plastic bottle": 82.8,
    "bottle": 82.8,
    "tree planted": 21000.0,  # rough annual absorption
    "compost bin": 5000.0,
    "drive 1km": -170.0,
    "meatless meal": 1500.0,
    "reusable bag": 15.0,
    "flight": -250000.0,
    "litter": 50.0
}

class CarbonEstimate(BaseModel):
    co2_grams: float = Field(description="Estimated grams of CO2 saved (positive) or emitted (negative) per single unit.")

estimate_parser = JsonOutputParser(pydantic_object=CarbonEstimate)

estimate_prompt = PromptTemplate(
    template="""You are a Carbon Emissions Data Scientist.
Estimate the CO2 footprint (in grams) for a single unit of the following category: {category}.
If the action saves CO2 (like recycling or planting), return a positive number.
If the action emits CO2 (like driving or burning), return a negative number.

{format_instructions}""",
    input_variables=["category"],
    partial_variables={"format_instructions": estimate_parser.get_format_instructions()}
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.1, 
    max_retries=1, 
    timeout=30
)
estimate_chain = estimate_prompt | llm | estimate_parser

def get_co2_impact(category: str, quantity: float) -> float:
    category_lower = category.lower()
    
    # Check direct match
    if category_lower in EMISSION_FACTORS:
        unit_co2 = EMISSION_FACTORS[category_lower]
        return unit_co2 * quantity
        
    # Check partial match
    for key, value in EMISSION_FACTORS.items():
        if key in category_lower or category_lower in key:
            return value * quantity
            
    # Fallback to LLM estimation
    try:
        print(f"Carbon Engine: Estimating CO2 for unknown category '{category}'...")
        result = estimate_chain.invoke({"category": category})
        unit_co2 = float(result.get("co2_grams", 0))
        return unit_co2 * quantity
    except Exception as e:
        print(f"Carbon Engine Error: {e}")
        return 0.0
