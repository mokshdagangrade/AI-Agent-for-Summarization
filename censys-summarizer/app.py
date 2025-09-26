import streamlit as st
import requests
import pandas as pd

# Base URL of your FastAPI app
BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Censys Summarizer UI", layout="wide")

st.title("Censys Summarizer Dashboard")

# Sidebar navigation
menu = ["Hosts Overview", "Host Details", "Q/A with Data", "Summarize Dataset", "Summarize Host"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Hosts Overview":
    st.header("All Hosts Overview")
    try:
        response = requests.get(f"{BASE_URL}/hosts")
        hosts = response.json()
        df = pd.DataFrame(hosts)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error fetching hosts: {e}")

elif choice == "Host Details":
    st.header("View Single Host Details")
    ip = st.text_input("Enter Host IP:")
    if st.button("Get Host Details") and ip:
        try:
            response = requests.get(f"{BASE_URL}/hosts/{ip}")
            host = response.json()
            st.json(host)
        except Exception as e:
            st.error(f"Host not found or error: {e}")

elif choice == "Q/A with Data":
    st.header("Ask a Question about the Dataset")
    question = st.text_area("Enter your question:")
    if st.button("Get Answer") and question:
        payload = {"question": question}
        try:
            response = requests.post(f"{BASE_URL}/qa-global", json=payload)
            answer = response.json()
            st.subheader("Answer")
            st.write(answer.get("answer"))
        except Exception as e:
            st.error(f"Error fetching answer: {e}")

elif choice == "Summarize Dataset":
    st.header("Dataset Summary")
    if st.button("Generate Summary"):
        try:
            response = requests.get(f"{BASE_URL}/summarize-dataset")
            summary = response.json().get("summary")
            st.write(summary)
        except Exception as e:
            st.error(f"Error generating summary: {e}")

elif choice == "Summarize Host":
    st.header("Summarize a Single Host")
    ip = st.text_input("Enter Host IP for Summary:")
    if st.button("Generate Host Summary") and ip:
        try:
            response = requests.get(f"{BASE_URL}/summarize-host/{ip}")
            summary = response.json().get("summary")
            st.subheader(f"Summary for {ip}")
            st.write(summary)
        except Exception as e:
            st.error(f"Host not found or error: {e}")
