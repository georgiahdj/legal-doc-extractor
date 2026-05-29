import streamlit as st
import json
import time
import pandas as pd
from extractor import pdf_to_images, save_results
from ollama_extractor import extract_from_pdf, check_ollama_connection
from evaluator import run_full_evaluation, format_evaluation_for_display
from prompts import PROMPTS

st.set_page_config(
    page_title="Legal Document Extractor",
    page_icon="📄",
    layout="wide"
)

with st.sidebar:
    st.title("⚙️ Advanced Settings")
    st.markdown("---")

    prompt_choice = st.selectbox(
        "Select extraction strategy:",
        options=["chain_of_thought", "zero_shot", "few_shot"],
        index=0,
        help="Advanced: Select the prompting strategy for the VLM"
    )

    st.markdown("---")
    st.subheader("ℹ️ About")
    st.markdown("""
    This tool extracts structured data from Greek property deeds using a
    Vision Language Model (VLM) running locally via Ollama.
    
    **Model:** Qwen2.5-VL 3B  
    **Powered by:** Ollama + Streamlit  
    **Assessment for:** Synthetica AI
    """)

st.title("📄 Legal Document Data Extractor")
st.markdown("*Synthetica AI — Technical Assessment*")
st.markdown("---")

tab1, tab2 = st.tabs(["📋 Extract", "📊 Evaluate"])

with tab1:

    ollama_ok = check_ollama_connection()
    if not ollama_ok:
        st.warning("⚠️ Ollama is starting up, please wait...")
    else:
        st.success("✅ Ollama is running and ready! (qwen2.5vl:3b)")

    st.markdown("### Upload your document")

    uploaded_file = st.file_uploader(
        "Upload a legal document (PDF)",
        type=["pdf"],
        help="Upload a Greek property deed (συμβόλαιο αγοραπωλησίας)"
    )

    if uploaded_file:
        st.info(f"📎 File uploaded: **{uploaded_file.name}**")

        if st.button("🔍 Extract Data", type="primary"):

            progress = st.progress(0)
            status = st.empty()

            status.text("📖 Reading PDF...")
            progress.progress(10)

            pdf_bytes = uploaded_file.read()

            with open("temp.pdf", "wb") as f:
                f.write(pdf_bytes)

            images = pdf_to_images("temp.pdf")
            total_pages = len(images)

            status.text(f"📄 Found {total_pages} pages")
            progress.progress(20)

            status.text("🤖 Extracting data with VLM...")

            selected_prompt = PROMPTS[prompt_choice]

            from extractor import merge_results
            from ollama_extractor import extract_from_page

            page_results = []
            for i, image_bytes in enumerate(images):
                status.text(f"🤖 Processing page {i+1}/{total_pages}...")
                from ollama_extractor import safe_extract_from_page
                result = safe_extract_from_page(image_bytes, selected_prompt)
                page_results.append(result)

                prog = 20 + int((i+1)/total_pages * 70)
                progress.progress(prog)

            status.text("🔗 Merging results...")
            final_result = merge_results(page_results)
            progress.progress(95)

            save_results(final_result, "results.json")
            progress.progress(100)
            status.text("✅ Done!")

            st.markdown("---")
            st.markdown("## 📊 Extracted Data")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 👥 Involved Parties")

                st.markdown("**📋 Contract**")
                st.write(f"Number: {final_result.get('contract_number', 'N/A')}")
                st.write(f"Date: {final_result.get('contract_date', 'N/A')}")

                st.markdown("**⚖️ Notary**")
                notary = final_result.get("notary", {})
                st.write(f"Name: {notary.get('name', 'N/A')}")
                st.write(f"Address: {notary.get('address', 'N/A')}")

                st.markdown("**🏦 Sellers**")
                sellers = final_result.get("sellers", [])
                if sellers:
                    for i, seller in enumerate(sellers):
                        with st.expander(f"Seller {i+1}: {seller.get('name', 'Unknown')}"):
                            st.write(f"AFM: {seller.get('afm', 'N/A')}")
                            st.write(f"Address: {seller.get('address', 'N/A')}")
                            st.write(f"ID: {seller.get('id_document', 'N/A')}")
                else:
                    st.write("No sellers found")

                st.markdown("**🏢 Buyers**")
                buyers = final_result.get("buyers", [])
                if buyers:
                    for i, buyer in enumerate(buyers):
                        with st.expander(f"Buyer {i+1}: {buyer.get('name', 'Unknown')}"):
                            st.write(f"AFM: {buyer.get('afm', 'N/A')}")
                            st.write(f"Address: {buyer.get('address', 'N/A')}")
                            st.write(f"ID: {buyer.get('id_document', 'N/A')}")
                else:
                    st.write("No buyers found")

                reps = final_result.get("representatives", [])
                if reps:
                    st.markdown("**👤 Representatives**")
                    for i, rep in enumerate(reps):
                        with st.expander(f"Rep {i+1}: {rep.get('name', 'Unknown')}"):
                            st.write(f"Represents: {rep.get('represents', 'N/A')}")
                            st.write(f"ID: {rep.get('id_document', 'N/A')}")

            with col2:
                st.markdown("### 🏠 Property Details")

                properties = final_result.get("properties", [])
                if properties:
                    for i, prop in enumerate(properties):
                        st.markdown(f"**Property {i+1}**")
                        with st.expander(f"{prop.get('type', 'Unknown')} — {prop.get('location', 'N/A')}"):
                            st.write(f"Type: {prop.get('type', 'N/A')}")
                            st.write(f"Location: {prop.get('location', 'N/A')}")
                            st.write(f"Municipality: {prop.get('municipality', 'N/A')}")
                            st.write(f"Block: {prop.get('block', 'N/A')}")
                            st.write(f"Area: {prop.get('area_sqm', 'N/A')} sqm")
                            st.write(f"Floor: {prop.get('floor', 'N/A')}")
                            st.write(f"KAEK: {prop.get('kaek', 'N/A')}")
                            st.write(f"Building Permit: {prop.get('building_permit', 'N/A')}")
                else:
                    st.write("No properties found")

            st.markdown("---")
            with st.expander("🔍 View Raw JSON"):
                st.json(final_result)

            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(
                    final_result,
                    ensure_ascii=False,
                    indent=2
                ),
                file_name="extracted_data.json",
                mime="application/json"
            )

with tab2:
    st.markdown("### 📊 Prompt Strategy Evaluation")
    st.markdown("""
    This tab compares the 3 prompt strategies on the first 3 pages
    of your document. It measures:
    - **Speed**: average time per page
    - **Accuracy proxy**: number of fields successfully extracted
    """)

    eval_file = st.file_uploader(
        "Upload PDF for evaluation",
        type=["pdf"],
        key="eval_uploader"
    )

    if eval_file:
        if st.button("▶️ Run Evaluation", type="primary"):

            with st.spinner("Running evaluation on 3 prompts × 3 pages..."):
                pdf_bytes = eval_file.read()
                with open("temp_eval.pdf", "wb") as f:
                    f.write(pdf_bytes)

                images = pdf_to_images("temp_eval.pdf")
                results = run_full_evaluation(images)

            st.success("✅ Evaluation complete!")

            st.markdown("### Results")
            display_data = format_evaluation_for_display(results)
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Speed (lower is better)**")
                speed_data = {
                    r["prompt_name"]: r["avg_time_per_page"]
                    for r in results
                }
                st.bar_chart(speed_data)

            with col2:
                st.markdown("**Fields Extracted (higher is better)**")
                accuracy_data = {
                    r["prompt_name"]: r["fields_extracted"]["total_filled"]
                    for r in results
                }
                st.bar_chart(accuracy_data)

            best = max(results, key=lambda x: x["fields_extracted"]["total_filled"])
            fastest = min(results, key=lambda x: x["avg_time_per_page"])

            st.markdown("### 🏆 Conclusions")
            st.success(f"Best accuracy: **{best['prompt_name']}** ({best['fields_extracted']['total_filled']} fields)")
            st.info(f"Fastest: **{fastest['prompt_name']}** ({fastest['avg_time_per_page']}s/page)")