from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Get API key from the environment variables
API_KEY = os.getenv("API_KEY")

# OpenAI API endpoint for chat models
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def classify_vehicle_with_prompt(year, make, model, trim):
    """
    Sends vehicle details (year, make, model, trim) to the GPT model with a detailed prompt and retrieves the classification.
    """
    if not API_KEY:
        return "Error: API key is missing. Please set it in the .env file."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Build details string dynamically based on whether trim is provided
    details = f"Year: {year}\nMake: {make}\nModel: {model}"
    if trim:
        details += f"\nTrim: {trim}"

    # Refined prompt to restrict GPT to only return the desired output format
    prompt = f"""
    You are a vehicle classification assistant. Your job is to classify vehicles based on their details into one of four size categories: Small, Medium, Large, or Extra Large. You must strictly follow the provided output format and avoid including unnecessary details or instructions.

    # Details
    {details}

    # Output Format
    Vehicle Classification: {{year make model trim}} - {{category}}

    The {{year make model trim}} is a {{brief description}}. Given its characteristics, it falls into the "{{category}}" category for vehicle sizes. Here's why:

    {{year make model trim}} - Key Attributes:
    - Type: {{type}}
    - Dimensions:
      - Length: {{length}}
      - Width: {{width}}
    - Passenger Capacity: {{capacity}}
    - Purpose: {{purpose}}

    Classification:
    - {{category}}: {{reasoning}}

    Therefore, the {{year make model trim}} fits best into the "{{category}}" vehicle category.

    Now classify the following vehicle and return only the result in the above output format without including unnecessary steps or explanations: {year} {make} {model} {trim if trim else ""}.
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a vehicle classification assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.5  # Lower temperature for deterministic responses
    }

    try:
        # Send request to OpenAI API
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Parse the JSON response
        result = response.json()
        raw_content = result.get("choices", [{}])[0].get(
            "message", {}).get("content", "No classification found.")

        # Validate response format
        if "Vehicle Classification" not in raw_content:
            return f"GPT Response Error: Unexpected output - {raw_content}"

        return raw_content

    except requests.exceptions.RequestException as e:
        return f"Error communicating with the GPT API: {e}"


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Renders the home page and handles form submission.
    """
    if request.method == "POST":
        # Get user input from form
        year = request.form.get("year", "").strip()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        trim = request.form.get("trim", "").strip()  # Optional field

        # Validate required inputs
        if not year or not make or not model:
            return render_template(
                "index.html",
                error="Year, Make, and Model are required. Please provide them."
            )

        # Call classification function with inputs (pass empty string for trim if not provided)
        classification_result = classify_vehicle_with_prompt(year, make, model, trim)
        return render_template("index.html", result=classification_result)

    # Render the home page
    return render_template("index.html")


if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)
