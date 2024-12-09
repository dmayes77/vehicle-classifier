# vehicle-classifier
Vehicle Classifier: A Flask web app that classifies vehicles into size categories (Small, Medium, Large, Extra Large) based on length, width, and capacity. Integrates with the OpenAI API for detailed vehicle data. User-friendly interface, robust error handling, and dynamic feedback. Built with Python, Flask, HTML/CSS, and JavaScript.

# 🚗 Vehicle Classifier

A Flask web app that classifies vehicles into categories (Small, Medium, Large, Extra Large) based on their dimensions and passenger capacity. Integrates with the OpenAI API for detailed vehicle information.

## Features

- 🏎️ **Vehicle Size Classification**
- 📊 **Dynamic Feedback** based on user input
- 🌐 **OpenAI API Integration** for detailed data
- 🚦 **Error Handling** and user-friendly interface

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/vehicle-classifier.git
    cd vehicle-classifier
    ```

2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up your `.env` file with the following:
    ```
    API_KEY=your_openai_api_key
    ```

5. Run the Flask app:
    ```bash
    flask run
    ```

6. Visit `http://127.0.0.1:5000` in your browser.

## Usage

1. Enter the **Year**, **Make**, **Model**, and optionally the **Trim**.
2. Submit the form to classify the vehicle.
3. View detailed vehicle classification results.

## Technologies Used

- **Python** & **Flask**
- **HTML/CSS** & **JavaScript**
- **OpenAI API**

## License

This project is licensed under the MIT License.

## Contribution

Contributions are welcome! Please fork the repository and submit a pull request.

---

Let me know if you need any adjustments!

