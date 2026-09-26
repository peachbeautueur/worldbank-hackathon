from flask import Flask, jsonify
from flask_cors import CORS
from importlib import import_module

Global = import_module('global').Global

app = Flask(__name__)
CORS(app)
global_instance = Global()

@app.route('/api/get_non_null_data_percentage', methods=['GET'])
def get_non_null_data_percentage():
    app.logger.info("get_non_null_data_percentage() ran")
    return jsonify({'non_null_data_percentage': global_instance.get_non_null_data_percentage()})

if __name__ == '__main__':
   app.run(debug=True, port=5001)