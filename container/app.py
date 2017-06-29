"""
Docker container server to handle individual submission
Usage: Gets submission url through HTTP POST from the grader_server
    Invokes simple_grader to process the submission
Author: Zhipeng Yan
Date: Apr 30 2017
"""

from flask import Flask, request, jsonify
import os
import json
from simple_grader import SimpleGrader


app = Flask(__name__)
grader = SimpleGrader('/app')


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route("/shutdown", methods=['POST'])
def shutdown():
    shutdown_server()
    return "Docker server shutting down\n"


@app.route("/grade", methods=['POST'])
def grade():
    data = request.get_json(force=True)
    xqueue_body = json.loads(data['xqueue_body'])
    section_name = xqueue_body['grader_payload']  # ps1
    submission_files = json.loads(data['xqueue_files'])
    submission_url = submission_files['problem1.ipynb']

    feedback = grader.grade(section_name, submission_url)
    return jsonify(feedback)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
