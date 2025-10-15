import streamlit as st
import random
import base64
from pathlib import Path

# Sample food data (can be expanded or loaded from a database)
FOOD_DATA = {
    "Apple": {"Carb": 14, "Protein": 0.3, "Fat": 0.2, "Dietary fiber": 2.4},
    "Banana": {"Carb": 23, "Protein": 1.1, "Fat": 0.3, "Dietary fiber": 2.6},
    "Chicken Breast": {"Carb": 0, "Protein": 31, "Fat": 3.6, "Dietary fiber": 0},
    "Brown Rice": {"Carb": 23, "Protein": 2.7, "Fat": 0.9, "Dietary fiber": 3.5},
    "Broccoli": {"Carb": 7, "Protein": 2.8, "Fat": 0.4, "Dietary fiber": 2.6},
}

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_image_as_page_bg(img_path):
    """Set a base64-encoded image as the page background. Handles png/jpg/jpeg and falls back gracefully."""
    path = Path(img_path)
    if not path.exists():
        # No image found; do nothing
        return

    bin_str = get_base64_of_bin_file(path)
    # Infer MIME from suffix
    suffix = path.suffix.lower()
    if suffix in ['.jpg', '.jpeg']:
        mime = 'image/jpeg'
    elif suffix in ['.png']:
        mime = 'image/png'
    else:
        # default to octet-stream if unknown
        mime = 'application/octet-stream'

    # Use double braces for literal CSS braces when using an f-string
    # Provide a fallback gradient in case image inlining is blocked
    page_bg_img = f'''
    <style>
    /* Make the background cover the whole page and apply a subtle overlay */
    html, body, .stApp, [data-testid="stAppViewContainer"] {{{{
        background-image: url("data:{mime};base64,{bin_str}"), linear-gradient(135deg, #e0f7fa, #e8f5e9) !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        background-blend-mode: overlay !important;
    }}}}

    /* Also target main content container used by newer Streamlit versions */
    [data-testid="stAppViewContainer"] > div, [data-testid="stAppViewContainer"] > main {{{{
        background: transparent !important;
    }}}}

    /* Add a subtle dim overlay so content remains readable */
    .bg-overlay {{{{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.22) !important;
        z-index: 0;
        pointer-events: none;
    }}}}
    </style>
    <div class="bg-overlay"></div>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide")
    
    # Set background image
    set_image_as_page_bg('background.jpg')

    # Modern UI / glassmorphism styles
    st.markdown('''
    <style>
    /* Card container */
    [data-testid="stAppViewContainer"] .ppgi-card, .ppgi-card {
        backdrop-filter: blur(8px) saturate(120%) !important;
        background: linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,255,255,0.55)) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px rgba(31,38,135,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        z-index: 1 !important;
        max-width: 1100px !important;
        margin: 24px auto !important;
    }

    /* Headings */
    h1, .stTitle {
        letter-spacing: 0.5px;
        color: #083d77;
    }

    /* Buttons */
    [data-testid="stAppViewContainer"] .stButton>button, .stButton>button {
        background: linear-gradient(90deg,#4facfe,#00f2fe) !important;
        color: #03396c !important;
        border: none !important;
        padding: 10px 18px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Inputs spacing */
    [data-testid="stAppViewContainer"] .stTextInput>div>div>input, [data-testid="stAppViewContainer"] .stNumberInput>div>div>input, textarea {
        border-radius: 8px !important;
        padding: 8px 10px !important;
    }

    /* Ensure the card sits above background overlay */
    [data-testid="stAppViewContainer"] > div:first-child, .stApp > div:first-child {
        position: relative !important;
        z-index: 2 !important;
    }
    </style>
    ''', unsafe_allow_html=True)

    # Wrap content in a card
    st.markdown('<div class="ppgi-card">', unsafe_allow_html=True)

    st.title("Personalized Postprandial Glycemic Index (PPGI) Prediction")

    st.markdown('''
    <style>
    .big-font {
        font-size:20px !important;
    }
    .st-emotion-cache-1r4qj8v {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    ''', unsafe_allow_html=True)


    st.markdown("""    **About Us**

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
        family_history = st.selectbox("Family History (e.g., diabetes, heart disease)",
                                      ["No", "Yes - Mother", "Yes - Father", "Yes - Father, Mother"] )
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
    # Close the card div
    st.markdown('</div>', unsafe_allow_html=True)
if __name__ == "__main__":
    main()

