from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests
import re

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Get API key from the environment variables
API_KEY = os.getenv("API_KEY")

# OpenAI API endpoint for chat models
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def classify_vehicle_size(length, width):
    """
    Classify the vehicle size based on its dimensions using the new sizing logic.
    """
    if length <= 175 and width <= 75:
        return "Small"
    elif 175 <= length <= 202 and width <= 80:
        return "Medium"
    elif 202 <= length <= 225 and width <= 80:
        return "Large"
    else:
        return "Extra Large"


def extract_details_from_response(response):
    """
    Extract vehicle details (type, length, width, passenger capacity, purpose) from GPT response.
    """
    details = {}

    # Extract dimensions
    length_match = re.search(r"Length: (\d+\.?\d*)", response)
    width_match = re.search(r"Width: (\d+\.?\d*)", response)
    details["length"] = float(length_match.group(1)) if length_match else None
    details["width"] = float(width_match.group(1)) if width_match else None

    # Extract type
    type_match = re.search(r"Type: (.+)", response)
    details["type"] = type_match.group(1).strip() if type_match else "Unknown"

    # Extract passenger capacity
    capacity_match = re.search(r"Passenger Capacity: (\d+)", response)
    details["capacity"] = int(capacity_match.group(1)) if capacity_match else None

    # Extract purpose
    purpose_match = re.search(r"Purpose: (.+)", response)
    details["purpose"] = purpose_match.group(1).strip() if purpose_match else "Unknown"

    return details


def call_gpt_for_vehicle_info(year, make, model, trim):
    """
    Sends vehicle details (year, make, model, trim) to GPT for detailed information.
    """
    if not API_KEY:
        return "Error: API key is missing. Please set it in the .env file."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    details = f"Year: {year}\nMake: {make}\nModel: {model}"
    if trim:
        details += f"\nTrim: {trim}"

    # Detailed prompt
    prompt = f"""
    You are a vehicle classification assistant. Your job is to classify vehicles based on their details into one of four size categories: Small, Medium, Large, or Extra Large. Additionally, provide detailed vehicle attributes, including type, dimensions (length and width), passenger capacity, and purpose.

    # Details
    {details}

    # Output Format
    Vehicle Classification: {{year make model trim}} - {{category}}

    The {{year make model trim}} is a {{brief description}}. Here are its key attributes:

    - Type: {{type}}
    - Dimensions:
      - Length: {{length}}
      - Width: {{width}}
    - Passenger Capacity: {{capacity}}
    - Purpose: {{purpose}}

    Now classify the vehicle and provide detailed attributes. Return only the specified format.
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a vehicle classification assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No information found.")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with the GPT API: {e}"


def classify_vehicle_based_on_gpt(year, make, model, trim):
    """
    Retrieves vehicle details from GPT, reclassifies using local sizing logic,
    and returns detailed classification information.
    """
    gpt_response = call_gpt_for_vehicle_info(year, make, model, trim)

    # Extract details from GPT response
    details = extract_details_from_response(gpt_response)

    if details["length"] and details["width"]:
        # Classify the vehicle locally based on extracted dimensions
        local_category = classify_vehicle_size(details["length"], details["width"])
        return f"""
        Vehicle Classification: {year} {make} {model} {trim} - {local_category}

        The {year} {make} {model} is a {details['type']}. Given its characteristics, it falls into the "{local_category}" category for vehicle sizes. Here's why:

        {year} {make} {model} - Key Attributes:
        - Type: {details['type']}
        - Dimensions:
          - Length: {details['length']} inches
          - Width: {details['width']} inches
        - Passenger Capacity: {details['capacity']}
        - Purpose: {details['purpose']}

        Classification:
        - {local_category}: Based on its dimensions, passenger capacity, and purpose, the {year} {make} {model} is classified as a {local_category} vehicle.

        Therefore, the {year} {make} {model} fits best into the "{local_category}" vehicle category.
        """
    else:
        return "Error: Could not extract complete details from GPT response."


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Renders the home page and handles form submission.
    """
    if request.method == "POST":
        year = request.form.get("year", "").strip()
        make = request.form.get("make", "").strip().capitalize()  # Capitalize first letter
        model = request.form.get("model", "").strip().capitalize()  # Capitalize first letter
        trim = request.form.get("trim", "").strip()

        if not year or not make or not model:
            return render_template("index.html", error="Year, Make, and Model are required.")

        classification_result = classify_vehicle_based_on_gpt(year, make, model, trim)
        return render_template("index.html", result=classification_result)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
