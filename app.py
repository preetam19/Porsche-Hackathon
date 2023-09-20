from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    # Save the file or process it accordingly
    file.save(f'./uploads/{file.filename}')  # saves the file in a directory named 'uploads'

    return jsonify({"message": "File successfully uploaded"}), 200

if __name__ == "__main__":
    app.run(debug=True)
