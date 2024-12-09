from flask import Flask, render_template, request
from markupsafe import Markup
from dotenv import load_dotenv
from functools import lru_cache

import os
import time
import requests
import json
import logging
import re

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Get API key from the environment variables
API_KEY = os.getenv("API_KEY")

# OpenAI API endpoint for chat models
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)


def categorize_vehicle(length, width, capacity):
    """
    Categorize vehicle based on length, width, and passenger capacity, and provide a dynamic human-friendly reason.
    """
    length = length if length is not None else 0
    width = width if width is not None else 0

    if length <= 0 or width <= 0:
        return "Invalid inputs", "Please provide valid positive numbers for length and width."

    capacity_description = f"{capacity} passengers" if capacity is not None else "an unspecified number of passengers"

    if length <= 170 and width <= 75 and (capacity is None or capacity <= 3):
        return "Small", f"<p>With a length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this compact vehicle is ideal for city driving, easy parking, and daily commuting.</p>"
    elif length <= 220 and width <= 80 and (capacity is None or capacity <= 5):
        return "Medium", f"<p>Measuring {length} inches in length and {width} inches in width, with seating for {capacity_description}, this vehicle offers a great balance of space and maneuverability for small families and everyday use.</p>"
    elif length <= 235 and width <= 85 and (capacity is None or capacity <= 7):
        return "Large", f"<p>With a length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this spacious vehicle is perfect for larger families, road trips, and group outings.</p>"
    else:
        return "Extra Large", f"<p>With an impressive length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this vehicle offers maximum space and comfort, making it ideal for big families, long road trips, or those who love extra room.</p>"


from functools import lru_cache
import time
import requests
import json
import logging
import re

# Caching results to avoid redundant API calls
@lru_cache(maxsize=100)
def call_gpt_for_vehicle_info(year, make, model, trim):
    """
    Sends vehicle details (year, make, model, trim) to GPT for detailed classification and attributes.
    Retries up to 5 times with a 1-second wait between calls until length and width are valid.
    """
    if not API_KEY:
        raise ValueError("Error: API key is missing. Please set it in the .env file.")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    details = f"Year: {year}\nMake: {make}\nModel: {model}"
    if trim:
        details += f"\nTrim: {trim}"

    prompt = f"""
    Classify the following vehicle into one of four size categories: Small, Medium, Large, or Extra Large. 
    Provide vehicle type, dimensions (length and width), passenger capacity, and purpose in JSON format.

    # Details
    {details}

    # Output Format (JSON)
    {{
        "category": "Small/Medium/Large/Extra Large",
        "type": "Type of vehicle",
        "length": "Length in inches",
        "width": "Width in inches",
        "capacity": "Number of passengers",
        "purpose": "Purpose of the vehicle"
    }}
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You classify vehicles by size and attributes."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,  # Reduced token limit
        "temperature": 0.5
    }

    max_retries = 5
    retry_count = 0
    gpt_response = None

    while retry_count < max_retries:
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content")

            logging.debug(f"GPT Response: {content}")

            gpt_response = json.loads(content) if content else {"error": "No information found."}

            # Check if length and width are valid numbers
            length = gpt_response.get("length")
            width = gpt_response.get("width")

            if length and width and length != "Unknown" and width != "Unknown":
                break

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logging.error(f"Error communicating with the GPT API or parsing JSON: {e}")
            gpt_response = {"error": f"Error communicating with the GPT API or parsing JSON: {e}"}

        retry_count += 1
        logging.debug(f"Retry attempt {retry_count}")
        time.sleep(1)  # Reduced retry delay to 1 second

    return gpt_response if gpt_response else {"error": "No information found after multiple attempts."}


def classify_vehicle_based_on_gpt(year, make, model, trim):
    """
    Retrieves vehicle details from GPT, reclassifies using local sizing logic,
    and returns custom HTML classification information with reasons.
    """
    gpt_response = call_gpt_for_vehicle_info(year, make, model, trim)

    if "error" in gpt_response:
        return Markup(f"<p class='error-message'>{gpt_response['error']}</p>")

    # Extract attributes from the response
    category = gpt_response.get("category", "Unknown")
    vehicle_type = gpt_response.get("type", "Unknown")
    length = gpt_response.get("length", None)
    width = gpt_response.get("width", None)
    capacity = gpt_response.get("capacity", None)
    purpose = gpt_response.get("purpose", "Unknown")

    # Clean and convert length and width to floats if they are strings
    def clean_dimension(value):
        try:
            return float(re.sub(r"[^\d.]", "", value))
        except (ValueError, TypeError):
            return 0

    length = clean_dimension(length)
    width = clean_dimension(width)

    try:
        capacity = int(re.sub(r"[^\d]", "", capacity)) if capacity else None
    except (ValueError, TypeError):
        capacity = None

    local_category, reason = categorize_vehicle(length, width, capacity)

    result_html = f"""
    <div class="result">
        <h2>Classification Results: {local_category}</h2>
        <div class="result-content">
            <p><strong>Vehicle:</strong> {year} {make} {model} {trim}</p>
            <p><strong>Type:</strong> {vehicle_type}</p>
            <p><strong>Length:</strong> {length if length else 'Unknown'} inches</p>
            <p><strong>Width:</strong> {width if width else 'Unknown'} inches</p>
            <p><strong>Passenger Capacity:</strong> {capacity if capacity is not None else 'Unknown'}</p>
            <p><strong>Purpose:</strong> {purpose}</p>
            <h3>Reason for Classification:</h3>
            {reason}
        </div>
    </div>
    """

    return Markup(result_html)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        year = request.form.get("year", "").strip()
        make = request.form.get("make", "").strip().title()
        model = request.form.get("model", "").strip().title()
        trim = request.form.get("trim", "").strip().title()

        if not year or not make or not model:
            return render_template("index.html", error="Year, Make, and Model are required.")

        classification_result = classify_vehicle_based_on_gpt(year, make, model, trim)
        return render_template("index.html", result=classification_result)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
