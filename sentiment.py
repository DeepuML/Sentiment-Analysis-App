import streamlit as st
from transformers import pipeline
from langdetect import detect
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
import json

# ========================
# Caching Models
# ========================
@st.cache_resource
def load_model(model_name):
    return pipeline("sentiment-analysis", model=model_name)

# ========================
# Preprocessing Functions
# ========================
def preprocess_text(text, lowercase=True, remove_punct=True):
    if lowercase:
        text = text.lower()
    if remove_punct:
        text = text.translate(str.maketrans('', '', string.punctuation))
    return text.strip()

# ========================
# Detect Language
# ========================
def detect_language(text):
    try:
        return detect(text)
    except:
        return "Unknown"

# ========================
# Analyze Sentiment
# ========================
def analyze_sentiments(texts, model):
    results = model(texts)
    output = []
    for t, r in zip(texts, results):
        lang = detect_language(t)
        output.append({
            "Text": t,
            "Language": lang,
            "Sentiment": r["label"],
            "Confidence (%)": round(r["score"] * 100, 2),
            "Word Count": len(t.split()),
            "Character Count": len(t)
        })
    return pd.DataFrame(output)

# ========================
# Main App
# ========================
def main():
    st.set_page_config(page_title="💬 Ultimate Sentiment Analyzer", layout="wide")
    st.title("💬 Ultimate Real-Time Sentiment Analyzer")

    with st.sidebar:
        st.header("⚙️ Settings")

        # Model selection with proper Hugging Face IDs
        model_options = {
            "DistilBERT (English)": "distilbert-base-uncased-finetuned-sst-2-english",
            "RoBERTa (Twitter)": "cardiffnlp/twitter-roberta-base-sentiment-latest"
        }
        selected_model_label = st.selectbox("Select Transformer Model", list(model_options.keys()))
        model_name = model_options[selected_model_label]

        lowercase = st.checkbox("Convert to lowercase", value=True)
        remove_punct = st.checkbox("Remove punctuation", value=True)
        st.markdown("---")

        file = st.file_uploader("📤 Upload .txt or .csv file", type=["txt", "csv"])
        st.markdown("Or paste text below 👇")

    # Text Input or File Input
    if file:
        if file.name.endswith(".txt"):
            raw_text = file.read().decode("utf-8")
            texts = [line.strip() for line in raw_text.split("\n") if line.strip()]
        elif file.name.endswith(".csv"):
            df = pd.read_csv(file)
            texts = df.iloc[:, 0].dropna().tolist()
    else:
        input_text = st.text_area("Paste your text here (one entry per line):", height=200)
        texts = [line.strip() for line in input_text.split("\n") if line.strip()]

    # Preprocess
    texts = [preprocess_text(t, lowercase, remove_punct) for t in texts if t]

    analyze_button = st.button("🚀 Analyze", key="analyze_btn")
    if analyze_button and texts:
        model = load_model(model_name)
        df = analyze_sentiments(texts, model)

        # Tabs for views
        tab1, tab2, tab3 = st.tabs(["📋 Results Table", "📊 Visualizations", "📤 Export Data"])

        with tab1:
            st.subheader("📋 Sentiment Results")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.subheader("📊 Confidence by Sentiment")
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(data=df, x="Sentiment", y="Confidence (%)", hue="Sentiment", ax=ax)
            st.pyplot(fig)

            st.subheader("📈 Sentiment Distribution")
            pie_data = df["Sentiment"].value_counts()
            st.pyplot(pie_data.plot.pie(autopct='%1.1f%%', figsize=(6, 6), ylabel="").get_figure())

        with tab3:
            st.download_button("⬇️ Download as CSV", df.to_csv(index=False).encode("utf-8"), "results.csv", "text/csv")
            st.download_button("⬇️ Download as JSON", json.dumps(df.to_dict(orient="records"), indent=2).encode(), "results.json", "application/json")

        with st.expander("📌 Analysis Summary"):
            st.write(f"📝 Total entries: {len(df)}")
            st.write(f"📏 Average confidence: {df['Confidence (%)'].mean():.2f}%")
            st.write(f"📚 Languages Detected: {', '.join(df['Language'].unique())}")

    elif analyze_button and not texts:
        st.warning("⚠️ Please enter or upload some text to analyze.")

if __name__ == "__main__":
    main()
