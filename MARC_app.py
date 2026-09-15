import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="MARC to Spreadsheet", layout="wide")

st.title("📚 MARC (Tagged Text) → Spreadsheet Tool")

# -----------------------------
# Session State Initialization
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = []

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# -----------------------------
# Helper Functions
# -----------------------------
def extract_subfields(line):
    matches = re.findall(r"\$([a-z])\s([^$]+)", line)
    return {code: value.strip() for code, value in matches}


def clean_text(text):
    return text.strip().rstrip(" /:,;")


def extract_year(text):
    match = re.search(r"\d{4}", text)
    return match.group(0) if match else text


def parse_marc_text(text):
    lines = text.split("\n")

    record = {
        "Subjects": "",
        "Title": "",
        "Author": "",
        "Other Authors": "",
        "Statement": "",
        "Edition": "",
        "Publisher": "",
        "Year": "",
        "ISBN": "",
    }

    other_authors = []

    for line in lines:
        line = line.strip()

        try:
            if line.startswith("020"):
                sub = extract_subfields(line)
                record["ISBN"] = clean_text(sub.get("a", ""))

            elif line.startswith("100"):
                sub = extract_subfields(line)
                record["Author"] = clean_text(sub.get("a", ""))

            elif line.startswith("245"):
                sub = extract_subfields(line)
                if "b" in sub:
                    record["Title"] = clean_text(sub.get("a", "")) + " : " + clean_text(sub.get("b", ""))
                else:
                    record["Title"] = clean_text(sub.get("a", ""))
                record["Statement"] = clean_text(sub.get("c", ""))

            elif line.startswith("250"):
                sub = extract_subfields(line)
                record["Edition"] = clean_text(sub.get("a", ""))
            
            elif line.startswith("264  1"):
                sub = extract_subfields(line)
                record["Publisher"] = clean_text(sub.get("b", ""))
                record["Year"] = extract_year(sub.get("c", ""))

            elif line.startswith("260"):
                sub = extract_subfields(line)
                if "b" in sub:
                    record["Publisher"] = clean_text(sub.get("a", "")) + " : " + clean_text(sub.get("b", ""))
                else:
                    record["Publisher"] = clean_text(sub.get("a", ""))
                record["Year"] = extract_year(sub.get("c", ""))
            
            elif line.startswith("700"):
                sub = extract_subfields(line)
                name = sub.get("a", "")
                role = sub.get("e", "")
                if name:
                    if role:
                        other_authors.append(f"{clean_text(name)} ({clean_text(role)})")
                    else:
                        other_authors.append(clean_text(name))

            elif line.startswith("650"):
                sub = extract_subfields(line)
                
                parts = []
                if "a" in sub:
                    parts.append(sub["a"])
                if "x" in sub:
                    parts.append(sub["x"])

                subject = " -- ".join(parts)

                if record["Subjects"]:
                    record["Subjects"] += "; " + subject
                else:
                    record["Subjects"] = subject

        except Exception:
            continue  # skip problematic lines safely

    record["Other Authors"] = "; ".join(other_authors)

    return record


def is_duplicate_isbn(new_record):
    for r in st.session_state.data:
        if r["ISBN"] and r["ISBN"] == new_record["ISBN"]:
            return True
    return False


# -----------------------------
# UI Layout
# -----------------------------
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("📥 Input MARC Record")

    st.session_state.input_text = st.text_area(
        "Paste MARC record here",
        height=400,
        value=st.session_state.input_text
    )

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("➕ Add Record"):
            if st.session_state.input_text.strip():
                parsed = parse_marc_text(st.session_state.input_text)

                if is_duplicate_isbn(parsed):
                    st.warning("⚠️ Duplicate ISBN detected")

                st.session_state.data.append(parsed)
                st.success("✅ Record added!")

            else:
                st.error("Please paste a MARC record first.")

    with col_btn2:
        if st.button("🧹 Clear Input"):
            st.session_state.input_text = ""

# -----------------------------
# Data Display
# -----------------------------
with col2:
    st.subheader("📊 Extracted Records")

    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df, use_container_width=True)

        # -----------------------------
        # Export Section
        # -----------------------------
        st.subheader("⬇️ Export")

        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                csv,
                "marc_records.csv",
                mime="text/csv"
            )

        with col_exp2:
            excel_file = "marc_records.xlsx"
            df.to_excel(excel_file, index=False)

            with open(excel_file, "rb") as f:
                st.download_button(
                    "Download Excel",
                    f,
                    excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # -----------------------------
        # Clear Data Button
        # -----------------------------
        if st.button("🗑️ Clear All Records"):
            st.session_state.data = []
            st.warning("All records cleared.")

    else:
        st.info("No records added yet.")