from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from src.agent_controller import AgentController
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Initialize your agent
agent_controller = AgentController()
agent = agent_controller.get_agent()

@app.route('/')
def index():
    return render_template('index.html')  # Your HTML file in templates folder

@app.route('/ask', methods=['POST'])
def ask():
    try:
        user_input = request.json.get('message', '')
        logging.info(f"User input: {user_input}")
        # Get response from your agent
        response = agent.chat(user_input)
        return jsonify({'response': response.response})  # send JSON back
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'response': "Sorry, something went wrong."}), 500

@app.route('/reset', methods=['POST'])
def reset():
    try:
        logging.info("Resetting agent chat history.")
        agent.reset()
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error resetting agent: {e}")
        return jsonify({'status': 'error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
