import streamlit as st
import asyncio
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import engine
import tools

st.set_page_config(page_title="Secure Enterprise AI Dashboard", page_icon="🔐", layout="wide")

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
    authenticator.login(location='main', fields={'Form name': 'Login to Super-Agent'})
except Exception as e:
    st.error(e)

authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")


# Add a sign-up expander if user is not logged in
if authentication_status != True:
    with st.expander("New User? Click here to Register"):
        try:
            # Correct parameter name is 'pre_authorized' instead of 'preauthorization'
            email_reg, username_reg, name_reg = authenticator.register_user(pre_authorized=None)
            if email_reg:
                st.success("User registered successfully! You can now log in above.")
                # Save updated credentials back to config.yaml
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

    # --- SIDEBAR KNOWLEDGE INGESTION ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Ingest Knowledge")
    uploaded_file = st.sidebar.file_uploader("Upload text/markdown files to ChromaDB", type=["txt", "md"])
    if uploaded_file is not None:
        file_text = uploaded_file.read().decode("utf-8")
        if st.sidebar.button("Vectorize & Ingest"):
            with st.sidebar:
                with st.spinner("Processing embeddings..."):
                    res_msg = tools.ingest_uploaded_document(file_text, uploaded_file.name)
                    st.success(res_msg)

    st.title("🤖 Enterprise AI Super-Agent & Tool Switchboard")
    st.markdown("ChromaDB Vector RAG + Async DDGS Web Search + Full Math Suite.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] in ["user", "assistant"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if user_prompt := st.chat_input("Ask your secure corporate agent..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            # Use a dynamic status label instead of hardcoding a RAG message
            with st.status("Processing request...", expanded=False) as status:
                api_messages = [{"role": m["role"], "content": m["content"], **({"name": m["name"]} if "name" in m else {})} for m in st.session_state.messages]
                
                reply, used_tool, updated_history = asyncio.run(engine.run_agent_turn_async(api_messages))
                
                if used_tool:
                    status.update(label=f"Tool executed: `{used_tool}`", state="complete", expanded=False)
                    st.session_state.messages = updated_history
                else:
                    status.update(label="Response generated", state="complete", expanded=False)

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

