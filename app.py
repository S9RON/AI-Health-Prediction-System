import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import re

# PAGE CONFIG
st.set_page_config(
    page_title="AI Health Prediction",
    page_icon="🩺",
    layout="wide"
)

# CUSTOM CSS
st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

h1 {
    color: #1f4e79;
}

.stButton>button {
    width: 100%;
    height: 45px;
    border-radius: 10px;
    border: none;
    background: linear-gradient(to right, #4facfe, #00f2fe);
    color: white;
    font-size: 16px;
    font-weight: bold;
}

.block {
    background-color: white;
    padding: 20px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# DATABASE
conn = sqlite3.connect("health.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    dob TEXT,
    email TEXT,
    glucose REAL,
    hemoglobin REAL,
    cholesterol REAL,
    remarks TEXT
)
""")

conn.commit()

# SIDEBAR
st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Go To",
    [
        "Add Patient",
        "View Patients",
        "Update Patient",
        "Delete Patient"
    ]
)

# AI PREDICTION
def generate_ai_remark(glucose, hemoglobin, cholesterol):

    if hemoglobin < 12:
        return "Possible Anemia Risk"

    elif glucose > 180:
        return "Possible Diabetes Risk"

    elif cholesterol > 240:
        return "High Cholesterol Risk"

    else:
        return "Patient appears Healthy"

# EMAIL VALIDATION
def validate_email(email):

    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    return re.match(pattern, email)

# PDF GENERATION
def generate_pdf(data):

    if not os.path.exists("reports"):
        os.makedirs("reports")

    filename = f"reports/{data['name']}_report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "AI HEALTH REPORT",
            styles['Title']
        )
    )

    story.append(Spacer(1, 20))

    details = [
        f"Full Name: {data['name']}",
        f"Date of Birth: {data['dob']}",
        f"Email: {data['email']}",
        f"Glucose: {data['glucose']}",
        f"Haemoglobin: {data['hemoglobin']}",
        f"Cholesterol: {data['cholesterol']}",
        f"Remarks: {data['remarks']}"
    ]

    for item in details:

        story.append(
            Paragraph(
                item,
                styles['BodyText']
            )
        )

        story.append(Spacer(1, 10))

    doc.build(story)

    return filename

# ADD PATIENT
if menu == "Add Patient":

    st.title("AI Health Prediction")

    with st.form("patient_form"):

        name = st.text_input("Full Name")

        dob = st.date_input(
            "Date of Birth",
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )

        email = st.text_input("Email Address")

        glucose = st.number_input(
            "Glucose",
            min_value=0.0
        )

        hemoglobin = st.number_input(
            "Haemoglobin",
            min_value=0.0
        )

        cholesterol = st.number_input(
            "Cholesterol",
            min_value=0.0
        )

        submit = st.form_submit_button("Save")

    if submit:

        if not validate_email(email):

            st.error("Invalid Email")

        else:

            remarks = generate_ai_remark(
                glucose,
                hemoglobin,
                cholesterol
            )

            cursor.execute("""
            INSERT INTO patients
            (
                name,
                dob,
                email,
                glucose,
                hemoglobin,
                cholesterol,
                remarks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                str(dob),
                email,
                glucose,
                hemoglobin,
                cholesterol,
                remarks
            ))

            conn.commit()

            st.success("Patient Added Successfully")

            st.info(remarks)

            patient_data = {
                "name": name,
                "dob": dob,
                "email": email,
                "glucose": glucose,
                "hemoglobin": hemoglobin,
                "cholesterol": cholesterol,
                "remarks": remarks
            }

            pdf_path = generate_pdf(patient_data)

            with open(pdf_path, "rb") as pdf_file:

                st.download_button(
                    label="Download PDF Report",
                    data=pdf_file,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )

# VIEW PATIENTS
elif menu == "View Patients":

    st.title("Patient Records")

    df = pd.read_sql_query(
        "SELECT * FROM patients",
        conn
    )

    st.dataframe(df)

# UPDATE PATIENT
elif menu == "Update Patient":

    st.title("Update Patient")

    patient_id = st.number_input(
        "Patient ID",
        min_value=1
    )

    new_remark = st.text_input(
        "New Remark"
    )

    if st.button("Update"):

        cursor.execute("""
        UPDATE patients
        SET remarks=?
        WHERE id=?
        """, (
            new_remark,
            patient_id
        ))

        conn.commit()

        st.success("Updated Successfully")

# DELETE PATIENT
elif menu == "Delete Patient":

    st.title("Delete Patient")

    patient_id = st.number_input(
        "Patient ID",
        min_value=1
    )

    if st.button("Delete"):

        cursor.execute("""
        DELETE FROM patients
        WHERE id=?
        """, (
            patient_id,
        ))

        conn.commit()

        st.success("Deleted Successfully")