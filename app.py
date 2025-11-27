# app.py
import streamlit as st
from llm_clients import generate_answer

st.set_page_config(page_title="Regulation Requirement Extractor", layout="wide")
st.title("📜 Regulation Requirement Extractor")
st.markdown("""
Paste any legislation or regulatory text below, and the AI will extract 
actionable engineering requirements for your product.
""")

# ----------------- Helpers -----------------
def chunk_text(text, max_chars=40000):
    """
    Split text into chunks of max_chars length.
    Tries to cut at the last period to avoid breaking sentences.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            period = text.rfind(".", start, end)
            if period != -1:
                end = period + 1
        chunks.append(text[start:end].strip())
        start = end
    return chunks

# ----------------- Streamlit UI -----------------
reg_text = st.text_area(
    label="Paste legislation / regulation text here",
    height=300,
    placeholder="Paste the full text of the regulation here..."
)

max_tokens = st.slider("Max tokens per chunk", min_value=100, max_value=3000, value=1000, step=50)

if st.button("Extract Requirements"):
    if not reg_text.strip():
        st.warning("Please paste some text before extracting requirements.")
    else:
        with st.spinner("Analyzing text with LLM..."):
            chunks = chunk_text(reg_text, max_chars=30000)
            all_results = []
            
            for i, chunk in enumerate(chunks):
                st.info(f"Processing chunk {i+1}/{len(chunks)}...")
                prompt = f"""
You are a compliance assistant. Extract all actionable engineering requirements
from the following regulatory text, keep only the most important part. Format them as a numbered list with clear instructions.

Regulatory Text:
{chunk}
"""
                try:
                    result = generate_answer(prompt, max_tokens=max_tokens)
                    all_results.append(result)
                except Exception as e:
                    st.error(f"Error while processing chunk {i+1}: {e}")

            final_output = "\n".join(all_results)
            st.success("✅ Extraction complete!")
            st.subheader("Extracted Requirements")
            st.text_area("Requirements", value=final_output, height=400)
