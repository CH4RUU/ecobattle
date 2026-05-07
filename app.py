import streamlit as st
import requests
£
API_URL = "https://ecobattle-backend.onrender.com"

st.set_page_config(page_title="EcoBattle", page_icon="🌍", layout="centered")

st.title(" EcoBattle: Earth Defense System")

# Initialize session state from backend if not present
if "synced" not in st.session_state:
    try:
        resp = requests.get(f"{API_URL}/state")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.total_score = data.get("total_score", 0)
            st.session_state.earth_health = data.get("earth_health", 100)
            st.session_state.current_level = data.get("level", "Seedling")
            st.session_state.total_co2_saved = data.get("total_co2_saved", 0.0)
        st.session_state.synced = True
    except Exception as e:
        st.warning("Could not connect to backend API. Please ensure it is running.")
        st.session_state.total_score = 0
        st.session_state.earth_health = 100
        st.session_state.current_level = "Seedling"
        st.session_state.total_co2_saved = 0.0

# Ensure we have defaults if API failed
total_score = st.session_state.get("total_score", 0)
earth_health = st.session_state.get("earth_health", 100)
current_level = st.session_state.get("current_level", "Seedling")
total_co2 = st.session_state.get("total_co2_saved", 0.0)

# Sidebar
st.sidebar.header("Player Stats")
st.sidebar.markdown(f"**Total Score:** {total_score}")
st.sidebar.markdown(f"**Current Level:** {current_level}")
st.sidebar.markdown(f"**Total CO₂ Saved:** {total_co2:,.1f} g")

health_emoji = "🌳" if earth_health > 50 else "🔥"
st.sidebar.markdown(f"**Earth Health {health_emoji}:** {earth_health}%")
st.sidebar.progress(earth_health / 100.0)

if earth_health <= 0:
    st.error("Game Over. The Earth has collapsed. Restart the server to try again.")
    st.stop()

# Action Input
st.subheader("What eco-action did you take today?")
action_input = st.text_input("Describe your action:", key="action_input")
category = st.selectbox("Category", ["nature", "energy", "waste", "water", "other"])

if st.button("Submit Action"):
    if action_input.strip():
        with st.spinner("Analyzing impact..."):
            payload = {
                "action_description": action_input,
                "category": category
            }
            try:
                res = requests.post(f"{API_URL}/action", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    
                    # Update local state
                    st.session_state.total_score = data.get("total_score", total_score)
                    st.session_state.earth_health = data.get("earth_health", earth_health)
                    st.session_state.current_level = data.get("current_level", current_level)
                    st.session_state.total_co2_saved = data.get("total_co2_saved", total_co2)
                    
                    if data.get("game_over"):
                        st.session_state.game_over_msg = data.get("message")
                        st.session_state.last_message = None
                    else:
                        st.session_state.game_over_msg = None
                        st.session_state.last_message = data.get("message")
                        st.session_state.last_co2 = data.get("co2_grams_saved", 0.0)
                        st.session_state.last_impact = data.get("points_impact", 0)
                        st.session_state.last_fact = data.get("environmental_fact", "")
                        
                        # Store choices in session state to render them persistently
                        if "available_choices" in data and data["available_choices"]:
                            st.session_state.available_choices = data["available_choices"]
                        else:
                            st.session_state.available_choices = []
                            
                    st.rerun()
                else:
                    st.error("Error communicating with the EcoBattle engine.")
            except Exception as e:
                st.error("Failed to connect to the backend server.")

# Display persistent messages
if st.session_state.get("game_over_msg"):
    st.error(st.session_state.game_over_msg)
elif st.session_state.get("last_message"):
    st.success(st.session_state.last_message)
    if st.session_state.get("last_co2", 0.0) != 0.0:
        st.info(f"**Impact:** You changed the world's CO2 by {st.session_state.last_co2:,.1f} grams! ({st.session_state.last_impact} pts)")
    if st.session_state.get("last_fact"):
        st.info(f"**Did you know?** {st.session_state.last_fact}")

# Display Choices if they exist in session state
if st.session_state.get("available_choices"):
    st.subheader("Accept a Challenge!")
    choices = st.session_state.available_choices
    if len(choices) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Choice A (The Sprint)")
            st.write(choices[0].get("task"))
            st.write(f"**Reward:** {choices[0].get('reward_points')} pts")
            if st.button("Accept Challenge A", key="btn_A"):
                payload = {
                    "user_id": "player1",
                    "challenge_id": choices[0].get("id", "A"),
                    "reward_points": choices[0].get("reward_points", 0)
                }
                res = requests.post(f"{API_URL}/select-challenge", json=payload)
                if res.status_code == 200:
                    st.success(res.json().get("message"))
                    st.session_state.available_choices = []
                    st.rerun()
                    
        with col2:
            st.markdown("### Choice B (The Marathon)")
            st.write(choices[1].get("task"))
            st.write(f"**Reward:** {choices[1].get('reward_points')} pts")
            if st.button("Accept Challenge B", key="btn_B"):
                payload = {
                    "user_id": "player1",
                    "challenge_id": choices[1].get("id", "B"),
                    "reward_points": choices[1].get("reward_points", 0)
                }
                res = requests.post(f"{API_URL}/select-challenge", json=payload)
                if res.status_code == 200:
                    st.success(res.json().get("message"))
                    st.session_state.available_choices = []
                    st.rerun()
