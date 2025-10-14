# streamlit_app.py

import streamlit as st
import random


def main():
    st.title("Predict Personalized GI")

    st.markdown("""
    **About Us**

    Welcome to Predict Personalized GI – a tool designed to help you understand and manage how your unique personal details influence the glycemic impact of foods in your diet.

    This web application was developed as part of a final-year undergraduate research project conducted by the Department of Food Science and Technology, Faculty of Agriculture, University of Peradeniya.

    Our mission is to empower individuals with personalized nutrition insights, moving beyond standard GI tables to provide predictions based on your own data.
    """)

    st.write("Provide input values (defaults set from provided feature vector) and the app will predict IAUC/GI")

    # Personal / anthropometric inputs (defaults from user-provided features)
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0.0, max_value=120.0, value=2.416109, format="%.6f")
    weight = st.number_input("Weight (kg)", min_value=0.0, value=2.829573, format="%.6f")
    height = st.number_input("Height (cm)", min_value=0.0, value=3.920458, format="%.6f")
    bmi = st.number_input("BMI (kg/m²)", min_value=0.0, value=0.374084, format="%.6f")
    waist = st.number_input("Waist circumference", min_value=0.0, value=0.794234, format="%.6f")
    hip = st.number_input("Hip circumference", min_value=0.0, value=0.0, format="%.6f", help="No default provided; enter measured hip circumference if available")
    wc_hc = st.number_input("WC / HC", min_value=0.0, value=0.906987, format="%.6f")

    st.write("---")
    st.subheader("Blood / Food features")
    blood_glucose = st.number_input("Blood glucose", min_value=0.0, value=11.289838, format="%.6f")

    st.write("---")
    st.write("Macronutrients / Composition (per 100 g food item)")
    moisture = st.number_input("Moisture (%)", min_value=0.0, max_value=100.0, value=36.667813, format="%.6f")
    protein = st.number_input("Protein (g)", min_value=0.0, value=33.837865, format="%.6f")
    carb = st.number_input("Carb (g / 100 g)", min_value=0.0, value=33.073373, format="%.6f")
    fat = st.number_input("Fat (g)", min_value=0.0, value=19.055226, format="%.6f")
    ash = st.number_input("Ash Content", min_value=0.0, max_value=100.0, value=5.506748, format="%.6f")
    dietary_fiber = st.number_input("Dietary Fiber", min_value=0.0, value=0.729844, format="%.6f")

    if st.button("Predict IAUC"):
        # Placeholder prediction (replace with model inference)
        iauc_pred = random.uniform(0, 500)
        st.success(f"Predicted IAUC: {iauc_pred:.2f}")

        st.write("### Input summary")
        st.write({
            "Name": name,
            "Age": age,
            "Weight (kg)": weight,
            "Height (cm)": height,
            "BMI": bmi,
            "Waist circumference": waist,
            "Hip circumference": hip,
            "WC/HC": wc_hc,
            "Blood glucose": blood_glucose,
            "Moisture (%)": moisture,
            "Protein (g)": protein,
            "Carb (g/100g)": carb,
            "Fat (g)": fat,
            "Ash Content": ash,
            "Dietary Fiber": dietary_fiber,
        })


if __name__ == "__main__":
    main()
