from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import logging
import json
import ollama
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRAPED_DATA_FILE = "scraped_data.json"

# Custom headers to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Function to check if a site allows scraping
def is_scrapable(url):
    try:
        robots_url = url.rstrip("/") + "/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        # Allow scraping if robots.txt is empty or allows user-agent "*"
        if not rp.default_entry or rp.can_fetch("*", url):
            return True

        return False  # Disallowed by robots.txt

    except Exception as e:
        logging.warning(f"Error checking robots.txt: {e}")
        return False  # Assume not scrappable

# Scrape website content
def scrape_website(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, timeout=60000)

            html_content = page.content()
            page.close()
            browser.close()

        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)

        # Store scraped data
        with open(SCRAPED_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"url": url, "content": text_content}, f, indent=4)

        return text_content

    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        return None  # Prevents app crash

# Route to check if a website is scrappable
@app.route("/check", methods=["POST"])
def check_site():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if is_scrapable(url):
        return jsonify({"message": "Website is scrappable"}), 200
    else:
        return jsonify({"message": "Website is not scrappable"}), 403

# Route to scrape the website
@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": f"Failed to scrape. Status code: {response.status_code}"}), response.status_code

        soup = BeautifulSoup(response.text, "html.parser")
        text_content = soup.get_text()

        return jsonify({"content": text_content})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to query the scraped data
@app.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        user_query = data.get("query")

        if not user_query:
            return jsonify({"error": "Query is required"}), 400

        # Load the scraped content from the stored file
        try:
            with open(SCRAPED_DATA_FILE, "r", encoding="utf-8") as f:
                scraped_data = json.load(f)
                website_content = scraped_data.get("content", "")
        except FileNotFoundError:
            return jsonify({"error": "No scraped data found. Please scrape a website first."}), 400

        # Process the query with DeepSeek LLM
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": f"Based on this content: {website_content}, answer: {user_query}"}]
        )

        # **Ensure JSON-serializable response**
        if isinstance(response, dict) and "message" in response:
            llm_response = response["message"]["content"]  # Extract content safely
        else:
            llm_response = str(response)  # Convert to string if not in expected format

        return jsonify({"response": llm_response})

    except Exception as e:
        logging.error(f"Query processing failed: {e}")
        return jsonify({"error": "Query processing failed."}), 500

# Serve index.html
@app.route("/")
def index():
    return render_template("index.html")

# Serve static files
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
