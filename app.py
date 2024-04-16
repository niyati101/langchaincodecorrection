from flask import Flask, request, render_template
import subprocess
import requests
import os
import tempfile

app = Flask(__name__)

# Store the current code in memory
current_code = ""
your_api_key = "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"

# Basic HTML template for the IDE interface
editor_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Code IDE</title>
</head>
<body>
    <h1>Code IDE</h1>
    <form method="post" action="/execute">
        <textarea name="code" rows="20" cols="80">{}</textarea><br>
        <label for="language">Select Language:</label>
        <select id="language" name="language">
            <option value="python">Python</option>
            <option value="java">Java</option>
        </select><br>
        <input type="submit" value="Execute">
    </form>
    <h2>Output:</h2>
    <pre>{}</pre>
    <h2>Error:</h2>
    <pre>{}</pre>
    <h2>Suggested Code:</h2>
    <pre>{}</pre>
    <h2>Chatbox:</h2>
    <form method="post" action="/generate_code">
        <input type="text" name="prompt" placeholder="Enter your prompt">
        <input type="submit" value="Generate Code">
    </form>
    <h2>Generated Code:</h2>
    <pre>{}</pre>
</body>
</html>
"""

# Dictionary to map language names to their corresponding file extensions
LANGUAGE_EXTENSIONS = {
    'python': 'py',
    'java': 'java',
}

def execute_code(code, language):
    try:
        if language == 'python':
            # Python execution
            result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=10)
            output = result.stdout
            error = result.stderr

        elif language == 'java':
            # Java execution
            with tempfile.TemporaryDirectory() as temp_dir:
                java_file_path = os.path.join(temp_dir, "Main.java")
                with open(java_file_path, "w") as java_file:
                    java_file.write('class Main { public static void main(String[] args) { ' + code + ' } }')

                javac_result = subprocess.run(f"javac {java_file_path}", shell=True, capture_output=True, text=True, cwd=temp_dir)
                if javac_result.returncode != 0:
                    return None, javac_result.stderr

                java_result = subprocess.run(f"java Main", capture_output=True, text=True, timeout=10, cwd=temp_dir)
                output = java_result.stdout
                error = java_result.stderr

        else:
            return None, f"Unsupported language: {language}"

        return output, error

    except subprocess.TimeoutExpired:
        return None, 'Code execution timed out.'
    except subprocess.CalledProcessError as e:
        return None, e.stderr

@app.route('/execute', methods=['POST'])
def execute():
    global current_code
    code = request.form.get('code', '')
    language = request.form.get('language', 'python')
    current_code = code
    output, error = execute_code(code, language)
    suggested_code = get_code_suggestions(code, language, your_api_key)
    return editor_template.format(code, output, error, suggested_code, "")

@app.route('/generate_code', methods=['POST'])
def generate_code():
    prompt = request.form.get('prompt', '')
    generated_code = generate_code_from_prompt(prompt, your_api_key)
    return editor_template.format(current_code, "", "", "", generated_code)

def get_code_suggestions(code, language, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Craft the chat prompt for better context
    prompt = f"This is a {language} code snippet. Can you improve it?\n{code}"
    data = {
        "model": "davinci-002",
        "prompt": prompt,
        "max_tokens": 250,
        "n": 1,
        "stop": None,
        "temperature": 0.7
    }

    response = requests.post("https://api.openai.com/v1/completions", headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        suggestion_text = response_data["choices"][0]["text"]
        return suggestion_text

    else:
        print(f"Error: {response.status_code}")
        return ""

def generate_code_from_prompt(prompt, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "davinci-002",
        "prompt": prompt,
        "max_tokens": 250,
        "n": 1,
        "stop": None,
        "temperature": 0.7
    }

    response = requests.post("https://api.openai.com/v1/completions", headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        generated_code = response_data["choices"][0]["text"]
        return generated_code

    else:
        print(f"Error: {response.status_code}")
        return ""

@app.route('/')
def home():
    global current_code
    return editor_template.format(current_code, "", "", "", "")

if __name__== '_main_':
    app.run(debug=True)