import requests
from bs4 import BeautifulSoup
import openai
from flask import Flask, render_template, request, redirect, url_for

from dotenv import load_dotenv
import os


load_dotenv()


app = Flask(__name__)

# Api key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

def fetch_site_data(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {"error": "Site not reachable"}

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "No Title"

        description = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            description = desc_tag.get("content", "")

        keywords = ""
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag:
            keywords = keywords_tag.get("content", "")

        text_snapshot = soup.get_text(separator=' ', strip=True)[:1000]

        return {
            "url": url,
            "title": title,
            "description": description,
            "keywords": keywords,
            "snapshot": text_snapshot
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_site(data):
    if "error" in data:
        return "Error fetching site"

    prompt_summary = f"""
    Based only on the following information, answer in ONE word only: "Safe" or "Suspicious".

    Website URL: {data['url']}
    Title: {data['title']}
    Description: {data['description']}
    Keywords: {data['keywords']}
    Page Text Snapshot:
    {data['snapshot']}

    Only reply with "Safe" if the website looks legitimate. 
    Reply with "Suspicious" if it might be fake, dangerous, or phishing.
    No explanation. No extra text. Only one word.
    """

    try:
        # result 
        response_summary = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_summary}],
            temperature=0,
        )
        summary = response_summary.choices[0].message.content.strip()

        return summary
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        url = request.form["url"]
        site_data = fetch_site_data(url)
        analysis = analyze_site(site_data)

        if analysis.lower() == "safe":
            result = "✅ Website is Safe"
        elif analysis.lower() == "suspicious":
            result = "⚠️ Website is Suspicious"
        else:
            result = "❗ Error analyzing site"

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
