import streamlit as st

st.set_page_config(
    page_title="RideWise AI",
    page_icon="🚕",
    layout="wide",
)

st.title("RideWise AI")
st.success("Streamlit is running. Your RideWise AI app is ready for development.")

st.markdown(
    """
    **RideWise AI** helps taxi drivers estimate fares and predict profit using
    rule-based pricing and machine learning.

    Use the sidebar pages to explore features as we build them.
    """
)
