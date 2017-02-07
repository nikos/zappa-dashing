#!/usr/bin/env python2
# -*- coding: utf-8

"""
Simple flask app to visualize how distribution of tracker data do
behave over the the last couple of days per customer.

Notes:
 * AWS Lambda uses Python 2.7
 * Zappa makes use of virtualenv, see README.md
"""

__author__ = "Niko Schmuck"
__version__ = "0.1.0"

from datetime import datetime, timedelta

import boto3
from flask import Flask, render_template, request, jsonify
from flask_cors import cross_origin, CORS

epoch = datetime.utcfromtimestamp(0)

app = Flask(__name__)
app.config.from_object('settings')
CORS(app)

# Static file delivery for CSS, JS and images
app.add_url_rule("/<path:filename>", view_func=app.send_static_file, endpoint="static")


def unix_time_seconds(dt):
    return (dt.replace(tzinfo=None) - epoch).total_seconds()


def eb_health(region):
    client = boto3.client('elasticbeanstalk', region_name=region)
    resp = client.describe_environment_health(AttributeNames=['Status', 'HealthStatus', 'Color', 'Causes'],
                                              EnvironmentName=app.config['EB_ENV_NAME'])
    # More info to display:
    # 'InstancesHealth':    {'Info': 0, 'Ok': 2, 'Unknown': 0, 'Severe': 0,
    #                         'Warning': 0, 'Degraded': 0, 'NoData': 0, 'Pending': 0},
    # 'StatusCodes':        {'Status3xx': 1219, 'Status2xx': 1082, 'Status5xx': 0, 'Status4xx': 0}}
    # 'ApplicationMetrics': {'Latency': {'P99': 0.002, ...

    return {
        'status': resp['Status'],  # Ready
        'health': resp['HealthStatus'],  # Ok
        'color': resp['Color'].lower(),  # red, green, ...
        'causes': resp['Causes']  # string array
    }


def metrics(region):
    client = boto3.client('cloudwatch', region_name=region)

    # http://boto3.readthedocs.io/en/latest/reference/services/cloudwatch.html#CloudWatch.Client.get_metric_statistics
    # http://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/aeb-metricscollected.html

    # Amazon CloudWatch retains metric data as follows:
    # - Data points with a period of 60 seconds (1 minute) are available for 15 days
    # - Data points with a period of 300 seconds (5 minute) are available for 63 days
    # - Data points with a period of 3600 seconds (1 hour) are available for 455 days (15 months)

    statistics_name = 'Sum'
    metric_name = 'RequestCount'

    response = client.get_metric_statistics(
        Namespace='AWS/ELB',
        MetricName=metric_name,
        Dimensions=[
            {
                'Name': 'LoadBalancerName',
                'Value': app.config['ELB_NAMES'][region]
            }
        ],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow(),
        Period=60,
        Statistics=[statistics_name],
    )

    # Turn the result into a Rickshaw-style series
    data = []

    for datapoint in response['Datapoints']:
        point = {
            'x': unix_time_seconds(datapoint['Timestamp']),
            'y': datapoint[statistics_name]
        }
        data.append(point)

    sorted_points = sorted(data, key=lambda point: point['x'])

    return {
        'name': metric_name,
        'points': sorted_points
    }


@app.route('/')
def main():
    return render_template('home.html')


@app.route('/status')
@cross_origin()
def status():
    region = request.args.get('region')
    health = eb_health(region)
    data = metrics(region)
    data['backgroundColor'] = health['color']

    # TODO: should we really return HTTP 5xx in case of problem? return jsonify(data), 503
    return jsonify(data)


if __name__ == '__main__':
    app.run()
