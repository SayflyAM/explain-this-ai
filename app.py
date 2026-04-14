from flask import Flask, request, render_template_string

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ExplainThis</title>
    <style>
        body {
            margin: 0;
            background: #e6ebf2;
            font-family: Arial, sans-serif;
            color: #1f2d3d;
        }
        .box {
            width: 760px;
            margin: 25px auto;
            background: #ffffff;
            border: 1px solid #8aa2be;
            padding: 15px;
        }
        h1 {
            margin: 0 0 10px 0;
            color: #003366;
        }
        .panel {
            border: 1px solid #b8c7d8;
            background: #f4f7fb;
            padding: 12px;
            margin-top: 12px;
        }
        textarea {
            width: 100%;
            height: 140px;
            border: 1px solid #9db0c5;
            padding: 6px;
            box-sizing: border-box;
            font-family: Arial, sans-serif;
        }
        button {
            margin-top: 10px;
            padding: 6px 14px;
            border: 1px solid #4f6b88;
            background: #d9e6f3;
            color: #0d2f52;
        }
        .result {
            min-height: 60px;
            border: 1px solid #c2d0df;
            background: #fff;
            padding: 10px;
            white-space: pre-wrap;
        }
        .error {
            color: #b00020;
            font-weight: bold;
        }
        @media (max-width: 820px) {
            .box {
                width: auto;
                margin: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>ExplainThis</h1>
        <p>sayf ammar</p>

        <form method="post" action="/simplify">
            <div class="panel">
                <label for="text">Enter Complex Text:</label><br>
                <textarea id="text" name="text" placeholder="Paste Arabic or English text here...">{{ text }}</textarea><br><br>

                <b>Select Language:</b><br>
                <label><input type="radio" name="language" value="english" {% if language == 'english' %}checked{% endif %}> English</label>
                <label><input type="radio" name="language" value="arabic" {% if language == 'arabic' %}checked{% endif %}> Arabic</label><br>

                <button type="submit">Simplify Text</button>
            </div>
        </form>

        <div class="panel">
            <h3>Simplified Explanation</h3>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% else %}
                <div class="result">{{ result }}</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


class FakeModel:
    # Very simple fake NLP model for training/demo only
    def __init__(self, language):
        self.language = language

    def generate(self, text):
        clean_text = " ".join(text.split())
        short_text = clean_text[:220]
        if len(clean_text) > 220:
            short_text += "..."

        if self.language == "arabic":
            return "شرح مبسط (تجريبي): " + short_text
        return "Dummy simplified explanation: " + short_text


# Load fake models one time (like startup model loading in architecture)
MODELS = {
    "english": FakeModel("english"),
    "arabic": FakeModel("arabic"),
}


def get_model(language):
    return MODELS.get(language, MODELS["english"])


@app.route("/", methods=["GET"])
def home():
    return render_template_string(
        PAGE,
        text="",
        language="english",
        result="Your simplified explanation will appear here.",
        error="",
    )


@app.route("/simplify", methods=["POST"])
def simplify():
    text = request.form.get("text", "")
    language = request.form.get("language", "english")

    if not text.strip():
        return render_template_string(
            PAGE,
            text=text,
            language=language,
            result="",
            error="Please enter text before clicking Simplify Text.",
        )

    model = get_model(language)
    result = model.generate(text)
    return render_template_string(PAGE, text=text, language=language, result=result, error="")


if __name__ == "__main__":
    app.run(debug=True)
