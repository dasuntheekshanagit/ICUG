
import streamlit as st
import random

# Sample food data (can be expanded or loaded from a database)
FOOD_DATA = {
    "Apple": {"Carb": 14, "Protein": 0.3, "Fat": 0.2, "Dietary fiber": 2.4},
    "Banana": {"Carb": 23, "Protein": 1.1, "Fat": 0.3, "Dietary fiber": 2.6},
    "Chicken Breast": {"Carb": 0, "Protein": 31, "Fat": 3.6, "Dietary fiber": 0},
    "Brown Rice": {"Carb": 23, "Protein": 2.7, "Fat": 0.9, "Dietary fiber": 3.5},
    "Broccoli": {"Carb": 7, "Protein": 2.8, "Fat": 0.4, "Dietary fiber": 2.6},
}

def main():
    st.set_page_config(layout="wide")
    st.title("Personalized Postprandial Glycemic Index (PPGI) Prediction")

    st.markdown("""
    **About Us**

    Welcome to Personalized Postprandial Glycemic Index (PPGI) Prediction – a tool designed to help you understand and manage how your unique personal details influence the glycemic impact of foods in your diet.

    This web application was developed as part of a final-year undergraduate research project conducted by the Department of Food Science and Technology, Faculty of Agriculture, University of Peradeniya.

    Our mission is to empower individuals with personalized nutrition insights, moving beyond standard GI tables to provide predictions based on your own data.
    """)

    st.write("--- ")
    st.subheader("Personal Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        age = st.number_input("Age (years)", min_value=0, max_value=120, value=30)
        weight = st.number_input("Weight (kg)", min_value=0.0, value=70.0, format="%.1f")

    with col2:
        wc = st.number_input("Waist Circumference (cm)", min_value=0.0, value=80.0, format="%.1f")
        birth_place = st.text_input("Birth Place", "")
        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])

    with col3:
        family_history = st.text_area("Family History (e.g., diabetes, heart disease)", "")
        physical_activity = st.selectbox("Physical Activity Level", 
                                         ["Sedentary (little or no exercise)", 
                                          "Lightly active (light exercise/sports 1-3 days/week)", 
                                          "Moderately active (moderate exercise/sports 3-5 days/week)", 
                                          "Very active (hard exercise/sports 6-7 days a week)", 
                                          "Extra active (very hard exercise/physical job)"])

    st.write("--- ")
    st.subheader("Food Item Information")

    food_selection_method = st.radio("Select Food Item", ("Choose from list", "Manually enter"))

    carb, protein, fat, dietary_fiber = 0.0, 0.0, 0.0, 0.0

    if food_selection_method == "Choose from list":
        food_item_name = st.selectbox("Food Item", list(FOOD_DATA.keys()))
        if food_item_name:
            selected_food = FOOD_DATA[food_item_name]
            carb = st.number_input("Carbohydrates (g/100g)", value=float(selected_food["Carb"]), format="%.1f", key="carb_auto")
            protein = st.number_input("Protein (g/100g)", value=float(selected_food["Protein"]), format="%.1f", key="protein_auto")
            fat = st.number_input("Fat (g/100g)", value=float(selected_food["Fat"]), format="%.1f", key="fat_auto")
            dietary_fiber = st.number_input("Dietary Fiber (g/100g)", value=float(selected_food["Dietary fiber"]), format="%.1f", key="fiber_auto")
    else: # Manually enter
        manual_food_name = st.text_input("Food Item Name", "")
        carb = st.number_input("Carbohydrates (g/100g)", value=0.0, format="%.1f", key="carb_manual")
        protein = st.number_input("Protein (g/100g)", value=0.0, format="%.1f", key="protein_manual")
        fat = st.number_input("Fat (g/100g)", value=0.0, format="%.1f", key="fat_manual")
        dietary_fiber = st.number_input("Dietary Fiber (g/100g)", value=0.0, format="%.1f", key="fiber_manual")

    st.write("--- ")

    if st.button("Predict PPGI"):
        # Placeholder for prediction logic
        predicted_ppgi = random.uniform(50, 100) # Example random PPGI value
        st.success(f"Predicted Postprandial Glycemic Index (PPGI): {predicted_ppgi:.2f}")

        st.write("### Input Summary")
        st.json({
            "Gender": gender,
            "Age": age,
            "Weight": weight,
            "Waist Circumference": wc,
            "Birth Place": birth_place,
            "Family History": family_history,
            "Blood Group": blood_group,
            "Physical Activity": physical_activity,
            "Food Item": food_item_name if food_selection_method == "Choose from list" else manual_food_name,
            "Carbohydrates": carb,
            "Protein": protein,
            "Fat": fat,
            "Dietary Fiber": dietary_fiber,
        })

if __name__ == "__main__":
    main()

