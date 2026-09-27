import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from importlib import import_module

Global = import_module('global').Global

app = Flask(__name__)
CORS(app)
global_instance = Global()

@app.route('/api/get_non_null_data_percentage', methods=['GET'])
def get_non_null_data_percentage():
    return jsonify({'non_null_data_percentage': global_instance.get_non_null_data_percentage()})

@app.route('/api/get_gdp_per_capita', methods=['GET'])
def get_gdp_per_capita():
    start_year = request.args.get('startYear', 2016, type=int)
    end_year = request.args.get('endYear', 2016, type=int)
    if start_year > end_year:
        return jsonify({'error': 'startYear must be less than or equal to endYear'}), 400
    data = global_instance.get_gdp_per_capita(start_year, end_year)
    records = json.loads(data.to_json(orient='records'))
    return jsonify({'gdp_per_capita': records})

@app.route('/api/get_gdp_per_capita_growth_trend', methods=['GET'])
def get_gdp_per_capita_growth_trend():
    start_year = request.args.get('startYear', 2016, type=int)
    end_year = request.args.get('endYear', 2016, type=int)
    if start_year > end_year:
        return jsonify({'error': 'startYear must be less than or equal to endYear'}), 400
    data = global_instance.get_gdp_per_capita_growth_trend(start_year, end_year)
    records = json.loads(data.to_json(orient='records'))
    return jsonify({'gdp_per_capita_growth_trend': records})

if __name__ == '__main__':
   app.run(debug=True, port=5001)