import streamlit as st
import asyncio
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import engine
import tools

st.set_page_config(page_title="Manipur Civic & RAG Assistant", page_icon="🏛️", layout="wide")

# --- LOAD CONFIGURATION FROM YAML ---
with open("config.yaml", "r") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["cookie_expiry_days"] if "cookie_expiry_days" in config["cookie"] else config["cookie"]["expiry_days"]
)

# --- RENDER LOGIN & REGISTER VIEWS ---
try:
    authenticator.login(location='main', fields={'Form name': 'Login to Manipur Assistant'})
except Exception as e:
    st.error(e)

authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")

# Add a sign-up expander if user is not logged in
if authentication_status != True:
    with st.expander("New User? Click here to Register"):
        try:
            email_reg, username_reg, name_reg = authenticator.register_user(pre_authorized=None)
            if email_reg:
                st.success("User registered successfully! You can now log in above.")
                with open("config.yaml", "w") as file:
                    yaml.dump(config, file, default_flow_style=False)
        except Exception as reg_err:
            st.error(reg_err)

if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password or sign up below.")
elif authentication_status == True:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome back, {name}!")

    # --- 🚨 EMERGENCY QUICK-DIAL BOARD (SIDEBAR) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Manipur Emergency Board")
    st.sidebar.markdown("Instant numbers (no AI required):")
    st.sidebar.markdown(
        """
        * **National Emergency:** `112`  
        * **Police Control Room (Imphal):** `0385-2450228`  
        * **Fire & Rescue:** `101`  
        * **Ambulance / Health Helpline:** `102`  
        * **MSPDCL Power Complaints:** `0385-2450050`  
        """
    )

    # --- 📍 DISTRICT SELECTOR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Target District")
    selected_district = st.sidebar.selectbox(
        "Select District / Region",
        ["General / All", "Imphal West", "Imphal East", "Thoubal", "Bishnupur", "Churachandpur", "Kakching", "Imphal Municipal Corporation"]
    )

    # --- SIDEBAR KNOWLEDGE INGESTION ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Ingest Knowledge")
    uploaded_file = st.sidebar.file_uploader(f"Upload text for {selected_district}", type=["txt", "md"])
    if uploaded_file is not None:
        file_text = uploaded_file.read().decode("utf-8")
        if st.sidebar.button("Vectorize & Ingest"):
            with st.sidebar:
                with st.spinner("Processing embeddings into ChromaDB..."):
                    res_msg = tools.ingest_uploaded_document(file_text, uploaded_file.name, district=selected_district)
                    st.success(res_msg)


    st.title("🏛️ Manipur Civic Assistant & RAG Switchboard")
    st.markdown("Local ChromaDB Vector RAG + Async DuckDuckGo Web Search.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] in ["user", "assistant"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if user_prompt := st.chat_input("Ask about water schedules, rules, or news..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.status("Processing request...", expanded=False) as status:
                # DYNAMIC FIX: Inject the selected location state directly into the background message history
                api_messages = []
                for m in st.session_state.messages:
                    msg_data = {"role": m["role"], "content": m["content"]}
                    if "name" in m:
                        msg_data["name"] = m["name"]
                    api_messages.append(msg_data)
                
                # Append a hidden directional context reminder specifying the active UI drop-down selection
                if api_messages and api_messages[-1]["role"] == "user":
                    api_messages[-1]["content"] += f" (Context: The user has selected the district: {selected_district} in the app settings.)"

                reply, used_tool, updated_history = asyncio.run(engine.run_agent_turn_async(api_messages))
                
                if used_tool:
                    status.update(label=f"Tool executed: `{used_tool}`", state="complete", expanded=False)
                    st.session_state.messages = updated_history
                else:
                    status.update(label="Response generated", state="complete", expanded=False)

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

