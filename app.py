from flask import Flask, render_template, request, jsonify
import bcrypt
import hashlib
import re
import math
import requests

def check_password_breach(password):
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Error"

    hashes = response.text.splitlines()

    for h in hashes:
        hash_suffix, count = h.split(":")
        if hash_suffix == suffix:
            return f"Breached ({count} times)"

    return "Safe"


def calculate_entropy(password):
    charset_size = 0

    if re.search(r"[a-z]", password):
        charset_size += 26
    if re.search(r"[A-Z]", password):
        charset_size += 26
    if re.search(r"[0-9]", password):
        charset_size += 10
    if re.search(r"[@$!%*?&#]", password):
        charset_size += 32

    if charset_size == 0:
        return 0

    entropy = math.log2(charset_size ** len(password))
    return round(entropy, 2)


def analyze_password_strength(password):
    score = 0

    # Length check
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10

    # Uppercase check
    if re.search(r"[A-Z]", password):
        score += 20

    # Lowercase check
    if re.search(r"[a-z]", password):
        score += 20

    # Digit check
    if re.search(r"[0-9]", password):
        score += 15

    # Special character check
    if re.search(r"[@$!%*?&#]", password):
        score += 15

    # Strength classification
    if score < 40:
        strength = "Weak"
    elif score < 70:
        strength = "Medium"
    else:
        strength = "Strong"

    return score, strength
def hash_sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()

def hash_bcrypt(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()
def password_suggestions(password):
    suggestions = []

    if len(password) < 12:
        suggestions.append("Increase password length to at least 12 characters")

    if not re.search(r"[A-Z]", password):
        suggestions.append("Add at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        suggestions.append("Add at least one lowercase letter")

    if not re.search(r"[0-9]", password):
        suggestions.append("Add at least one digit")

    if not re.search(r"[@$!%*?&#]", password):
        suggestions.append("Add special characters (@, #, $, etc.)")

    if not suggestions:
        suggestions.append("Your password is strong")

    return suggestions



app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_password", methods=["POST"])
def check_password():
    password = request.form.get("password")

    score, strength = analyze_password_strength(password)
    entropy = calculate_entropy(password)

    sha256_hash = hash_sha256(password)
    bcrypt_hash = hash_bcrypt(password)

    breach_status = check_password_breach(password)
    suggestions = password_suggestions(password)

    return jsonify({
        "strength": strength,
        "score": score,
        "entropy": entropy,
        "sha256": sha256_hash[:16] + "...",
        "bcrypt": bcrypt_hash[:20] + "...",
        "breach": breach_status,
        "suggestions": suggestions
    })


if __name__ == "__main__":
    app.run(debug=True)
