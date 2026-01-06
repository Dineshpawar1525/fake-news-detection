from flask import Flask, render_template, request, redirect, url_for, Response
import pandas as pd
import sklearn
import itertools
import numpy as np
import seaborn as sb
import re
import nltk
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from matplotlib import pyplot as plt
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.pipeline import Pipeline
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

app = Flask(__name__,template_folder='./templates',static_folder='./static')

def _train_fallback_pipeline():
    try:
        df = pd.read_csv('train.csv')
        X = df['Statement'].astype(str)
        y = df['Label'].astype(str)
        pipe = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english')),
            ('clf', PassiveAggressiveClassifier(max_iter=1000, random_state=42))
        ])
        pipe.fit(X, y)
        return pipe
    except Exception as e:
        print(f"Model training failed: {e}")
        return None

# Load trained pipeline if available; else train a fresh one
try:
    loaded_model = pickle.load(open('model.pkl', 'rb'))
except Exception as e:
    print(f"Falling back to training pipeline due to load error: {e}")
    loaded_model = _train_fallback_pipeline()

lemmatizer = WordNetLemmatizer()
stpwrds = set(stopwords.words('english'))

# Fit a TF-IDF vectorizer on training data for models that are not pipelines
try:
    _df_vec = pd.read_csv('train.csv')
    tfidf_v = TfidfVectorizer(stop_words='english')
    tfidf_v.fit(_df_vec['Statement'].astype(str))
except Exception as e:
    print(f"TF-IDF fit warning: {e}")
    tfidf_v = TfidfVectorizer(stop_words='english')

def fake_news_det(news):
    review = news
    review = re.sub(r'[^a-zA-Z\s]', '', review)
    review = review.lower()
    review = nltk.word_tokenize(review)
    local_corpus = []
    for y in review :
        if y not in stpwrds :
            local_corpus.append(lemmatizer.lemmatize(y))
    input_data = [' '.join(local_corpus)]
    # Predict with pipeline if available else with vectorized input
    if hasattr(loaded_model, 'named_steps'):
        prediction = loaded_model.predict(input_data)
    else:
        vectorized_input_data = tfidf_v.transform(input_data)
        prediction = loaded_model.predict(vectorized_input_data)
    pred = str(prediction[0]).strip().upper()
    if pred in ['0', 'FALSE', 'FAKE']:
        result = "Prediction of the News :  Looking Fake⚠ News📰 "
        print(result)
        return result
    else:
        result = "Prediction of the News : Looking Real News📰 "
        print(result)
        return result

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/index.html')
def index_html():
    # Support direct /index.html requests by redirecting to the home route
    return redirect(url_for('home'))


@app.route('/favicon.ico')
def favicon():
    # Prevent 404s for favicon; return empty response
    return Response(status=204)



@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        message = request.form['news']
        pred = fake_news_det(message)
        return render_template('index.html', prediction=pred)
    else:
        return render_template('index.html', prediction="Something went wrong")



if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)