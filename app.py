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
    indicator_code = request.args.get('indicator_code', "NY.GDP.PCAP.PP.CD", type=str)
    minimum_data_points_raw = request.args.get(
        'minimumDataPointsRequired', '3'
    )
    try:
        minimum_data_points_required = int(minimum_data_points_raw)
    except ValueError:
        return jsonify({'error': 'minimumDataPointsRequired must be an integer'}), 400
    if start_year > end_year:
        return jsonify({'error': 'startYear must be less than or equal to endYear'}), 400
    if minimum_data_points_required < 1:
        return jsonify({'error': 'minimumDataPointsRequired must be at least 1'}), 400
    data = global_instance.get_gdp_per_capita(
        start_year, end_year, minimum_data_points_required, indicator_code
    )
    records = json.loads(data.to_json(orient='records'))
    return jsonify({'gdp_per_capita': records})

@app.route('/api/get_gdp_per_capita_growth_trend', methods=['GET'])
def get_gdp_per_capita_growth_trend():
    start_year = request.args.get('startYear', 2016, type=int)
    end_year = request.args.get('endYear', 2016, type=int)
    indicator_code = request.args.get('indicator_code', "NY.GDP.PCAP.PP.CD", type=str)
    minimum_data_points_raw = request.args.get(
        'minimumDataPointsRequired', '3'
    )
    try:
        minimum_data_points_required = int(minimum_data_points_raw)
    except ValueError:
        return jsonify({'error': 'minimumDataPointsRequired must be an integer'}), 400
    if start_year > end_year:
        return jsonify({'error': 'startYear must be less than or equal to endYear'}), 400
    if minimum_data_points_required < 2:
        return jsonify({'error': 'minimumDataPointsRequired must be at least 2'}), 400
    data = global_instance.get_gdp_per_capita_growth_trend(
        start_year, end_year, minimum_data_points_required, indicator_code
    )
    records = json.loads(data.to_json(orient='records'))
    return jsonify({'gdp_per_capita_growth_trend': records})

@app.route('/api/get_gdp_per_capita_growth_additive', methods=['GET'])
def get_gdp_per_capita_growth_additive():
    start_year = request.args.get('startYear', 2016, type=int)
    end_year = request.args.get('endYear', 2016, type=int)
    indicator_code = request.args.get('indicator_code', "NY.GDP.PCAP.PP.CD", type=str)
    if start_year > end_year:
        return jsonify({'error': 'startYear must be less than or equal to endYear'}), 400
    data = global_instance.get_gdp_per_capita_growth_additive(
        start_year, end_year, indicator_code
    )
    records = json.loads(data.to_json(orient='records'))
    return jsonify({'get_gdp_per_capita_growth_additive': records})

if __name__ == '__main__':
   app.run(debug=True, port=5001)