from flask import Flask, render_template, request
from markupsafe import Markup
from dotenv import load_dotenv
from functools import lru_cache

import os
import time
import requests
import json
import re

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Get API key from the environment variables
API_KEY = os.getenv("API_KEY")

# OpenAI API endpoint for chat models
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def parse_capacity(capacity):
    """
    Parses the capacity string and returns a tuple with min and max capacities.
    Examples of valid inputs: '3-6 passengers', '5 passengers', '4-5', '3'.
    """
    if not capacity:
        return None, None

    numbers = list(map(int, re.findall(r'\d+', capacity)))

    if len(numbers) == 1:
        return numbers[0], numbers[0]  # Single capacity (e.g., '3 passengers')
    elif len(numbers) >= 2:
        return min(numbers), max(numbers)  # Range capacity (e.g., '3-6 passengers')

    return None, None


def categorize_vehicle(length, width, capacity):
    """
    Categorize vehicle based on length, width, and passenger capacity range,
    and provide a dynamic human-friendly reason.
    """
    length = length if length is not None else 0
    width = width if width is not None else 0

    if length <= 0 or width <= 0:
        return "Invalid inputs", "Please provide valid positive numbers for length and width."

    min_capacity, max_capacity = parse_capacity(capacity)
    capacity_description = f"{min_capacity}-{max_capacity} passengers" if min_capacity and max_capacity else "an unspecified number of passengers"

    if length <= 170 and width <= 75 and (max_capacity is None or max_capacity <= 3):
        return "Small", f"<p>With a length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this compact vehicle is ideal for city driving, easy parking, and daily commuting.</p>"
    elif length <= 220 and width <= 80 and (max_capacity is None or max_capacity <= 5):
        return "Medium", f"<p>Measuring {length} inches in length and {width} inches in width, with seating for {capacity_description}, this vehicle offers a great balance of space and maneuverability for small families and everyday use.</p>"
    elif length <= 235 and width <= 85 and (max_capacity is None or max_capacity <= 7):
        return "Large", f"<p>With a length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this spacious vehicle is perfect for larger families, road trips, and group outings.</p>"
    else:
        return "Extra Large", f"<p>With an impressive length of {length} inches, a width of {width} inches, and seating for {capacity_description}, this vehicle offers maximum space and comfort, making it ideal for big families, long road trips, or those who love extra room.</p>"


# Caching results to avoid redundant API calls
@lru_cache(maxsize=100)
def call_gpt_for_vehicle_info(year, make, model, trim):
    if not API_KEY:
        return {"error": "Error: API key is missing. Please set it in the .env file."}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    details = f"Year: {year}\nMake: {make}\nModel: {model}"
    if trim:
        details += f"\nTrim: {trim}"

    prompt = f"""
    Classify the following vehicle into one of four size categories: Small, Medium, Large, or Extra Large.
    Provide vehicle type, dimensions (length and width), passenger capacity (can be a range like 3-6), and purpose in JSON format.

    # Details
    {details}

    # Output Format (JSON)
    {{
        "category": "Small/Medium/Large/Extra Large",
        "type": "Type of vehicle",
        "length": "Length in inches",
        "width": "Width in inches",
        "capacity": "Capacity as a number or range (e.g., '3-6 passengers')",
        "purpose": "Purpose of the vehicle"
    }}
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You classify vehicles by size and attributes."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.5
    }

    max_retries = 5
    for retry_count in range(max_retries):
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content")

            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                return {"error": "No valid JSON found in the response."}

        except (requests.exceptions.RequestException, json.JSONDecodeError):
            time.sleep(1)

    return {"error": "No information found after multiple attempts."}


def classify_vehicle_based_on_gpt(year, make, model, trim):
    gpt_response = call_gpt_for_vehicle_info(year, make, model, trim)

    if "error" in gpt_response:
        return Markup(f"<p class='error-message'>{gpt_response['error']}</p>")

    vehicle_type = gpt_response.get("type", "Unknown")
    length = gpt_response.get("length", None)
    width = gpt_response.get("width", None)
    capacity = gpt_response.get("capacity", None)
    purpose = gpt_response.get("purpose", "Unknown")

    length = float(re.sub(r"[^\d.]", "", length) or 0)
    width = float(re.sub(r"[^\d.]", "", width) or 0)

    local_category, reason = categorize_vehicle(length, width, capacity)

    result_html = f"""
    <div class="result">
        <h2>Classification Results: {local_category}</h2>
        <div class="result-content">
            <p><strong>Vehicle:</strong> {year} {make} {model} {trim}</p>
            <p><strong>Type:</strong> {vehicle_type}</p>
            <p><strong>Length:</strong> {length} inches</p>
            <p><strong>Width:</strong> {width} inches</p>
            <p><strong>Passenger Capacity:</strong> {capacity}</p>
            <p><strong>Purpose:</strong> {purpose}</p>
            <h3>Reason for Classification:</h3>
            {reason}
        </div>
    </div>
    """

    return Markup(result_html)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


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
    app.run(debug=False)
