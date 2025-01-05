from flask import Flask, request, jsonify
from recommender import get_recs
app = Flask(__name__)

@app.route('/')
def main() :
    entry_msg  = '''
        <label for="user">Enter your Last.fm username:  </label>
        <input type="text" id="user" name="user"><br><br>
        <button type="button" onclick="getRecommendations()">submit</button><br><br>
        <div id="recommendations"></div>
        <script>
            async function getRecommendations() {
                document.getElementById('recommendations').innerHTML = "loading...<br><i>may take up to 2 minutes</i>";
                const user = document.getElementById('user').value
                const response = await fetch('/recommendations', {
                    method: "POST",
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ user })
                }).then(response => {
                    if (!response.ok) {
                    throw new Error('Network response was not ok');
                    }
                    return response.json()
                })
                .then(newUserData => {
                    console.log(newUserData.recommendations);
                    let string = "<ol>"
                    for (let i = 0; i < newUserData.recommendations.length; i++) {
                        string += "<li>" + newUserData.recommendations[i] + "</li>";
                    }
                    string += "</ol>"
                    document.getElementById('recommendations').innerHTML = string;
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        </script>
    '''
    return entry_msg

@app.route('/recommendations', methods = ['POST'])
def recommend() :
    user = request.get_json()['user']
    recommendations = get_recs(user)
    return jsonify({'recommendations' : recommendations})