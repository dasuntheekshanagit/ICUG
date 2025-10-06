# streamlit_app.py

import streamlit as st
import random

def main():
    st.title("IAUC Prediction Demo (Random Output)")

    st.write("Provide input values and the app will (randomly) predict IAUC")

    # Input fields
    name = st.text_input("Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0, max_value=120, value=30)
    weight = st.number_input("Weight (kg)", min_value=0.0, value=60.0)
    height = st.number_input("Height (cm)", min_value=0.0, value=170.0)
    bmi = st.number_input("BMI (kg/m²)", min_value=0.0, value=22.0)
    waist = st.number_input("Waist circumference (cm)", min_value=0.0, value=80.0)
    hip = st.number_input("Hip circumference (cm)", min_value=0.0, value=90.0)
    wc_hc = st.number_input("WC / HC ratio", min_value=0.0, value=waist / hip if hip != 0 else 0.0)

    birth_place = st.text_input("Birth place")
    family_history = st.selectbox("Family history diabetics", ["Yes", "No"])
    physical_activity = st.selectbox("Physical activity", ["Low", "Medium", "High"])
    health_problem = st.text_input("Health Problem (if any)")
    alcoholic = st.selectbox("Alcoholic", ["Yes", "No"])
    blood_group = st.text_input("Blood Group (e.g. A+, O-, etc.)")

    st.subheader("Food / Blood properties")
    food_item = st.text_input("Food Item")
    blood_glucose = st.number_input("Blood Glucose", min_value=0.0, value=90.0)

    st.write("---")
    st.write("Macronutrients / Composition (per 100 g food item)")
    carb = st.number_input("Carbohydrates (g / 100 g)", min_value=0.0, value=30.0)
    protein = st.number_input("Protein (g)", min_value=0.0, value=5.0)
    fat = st.number_input("Fat (g)", min_value=0.0, value=1.0)
    moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, value=60.0)
    ash = st.number_input("Ash Content (%)", min_value=0.0, max_value=100.0, value=1.0)
    dietary_fiber = st.number_input("Dietary Fiber (g)", min_value=0.0, value=2.0)

    if st.button("Predict IAUC"):
        # Here use your model; for demo we generate random number
        # For example, between 0 and 500
        iauc_pred = random.uniform(0, 500)
        st.success(f"Predicted IAUC: {iauc_pred:.2f}")

        # Optionally show input echo
        st.write("### Input summary")
        st.write({
            "Name": name,
            "Gender": gender,
            "Age": age,
            "Weight": weight,
            "Height": height,
            "BMI": bmi,
            "Waist": waist,
            "Hip": hip,
            "WC/HC": wc_hc,
            "Birth place": birth_place,
            "Family history": family_history,
            "Physical activity": physical_activity,
            "Health problem": health_problem,
            "Alcoholic": alcoholic,
            "Blood group": blood_group,
            "Food item": food_item,
            "Blood glucose": blood_glucose,
            "Carb": carb,
            "Protein": protein,
            "Fat": fat,
            "Moisture": moisture,
            "Ash": ash,
            "Dietary fiber": dietary_fiber
        })

if __name__ == "__main__":
    main()
