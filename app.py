from flask import Flask, render_template, request, redirect, url_for, Response, session, jsonify
import pandas as pd
import re
import nltk
import pickle
import time
import logging
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.pipeline import Pipeline
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
app.secret_key = 'fake_news_detector_secret_key_2024'  # Required for session management

# Constants
MAX_INPUT_LENGTH = 5000
SAMPLE_NEWS_FAKE = "The President announced today that the Earth is flat and space doesn't exist. Scientists have been lying to us for centuries about this."
SAMPLE_NEWS_REAL = "The World Health Organization (WHO) announced new guidelines for public health management and disease prevention strategies in collaboration with global health experts."

def _train_fallback_pipeline():
    """Removed - Use pre-trained model.pkl only"""
    return None

# Load trained pipeline (PRODUCTION: model.pkl is required)
try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        loaded_model = pickle.load(open('model.pkl', 'rb'))
    logger.info("✓ Model loaded successfully from model.pkl")
except FileNotFoundError:
    logger.error("✗ CRITICAL: model.pkl not found! App requires pre-trained model.")
    loaded_model = None
except Exception as e:
    logger.error(f"✗ Error loading model.pkl: {e}")
    loaded_model = None

lemmatizer = WordNetLemmatizer()
stpwrds = set(stopwords.words('english'))

# Initialize TF-IDF vectorizer (for non-pipeline models only)
tfidf_v = TfidfVectorizer(stop_words='english')


def preprocess_text(news):
    """
    Enhanced text preprocessing with repeated word removal and extra space handling.
    """
    try:
        # Remove special characters
        review = re.sub(r'[^a-zA-Z\s]', '', news)
        # Convert to lowercase
        review = review.lower()
        # Remove extra whitespace
        review = re.sub(r'\s+', ' ', review).strip()
        # Tokenize
        review = nltk.word_tokenize(review)
        # Remove stopwords and lemmatize
        local_corpus = []
        seen_words = set()
        for word in review:
            if word not in stpwrds:
                lemmatized = lemmatizer.lemmatize(word)
                # Avoid adding repeated words consecutively
                if lemmatized not in seen_words or len(seen_words) < 5:
                    local_corpus.append(lemmatized)
                    seen_words.add(lemmatized)
        
        return ' '.join(local_corpus)
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        return ""


def is_url(candidate: str) -> bool:
    """Simple URL detector to decide when to fetch remote content."""
    return bool(re.match(r'^https?://', candidate or '', re.IGNORECASE))


def extract_text_from_url(url: str) -> str:
    """Fetch page content and extract readable text."""
    try:
        headers = {
            'User-Agent': 'FakeNewsDetector/1.0 (+https://example.com)'
        }
        resp = requests.get(url, timeout=8, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        text = ' '.join(soup.stripped_strings)
        # Limit to reasonable length for the model
        return text[:MAX_INPUT_LENGTH]
    except Exception as e:
        logger.error(f"URL extraction failed: {e}")
        return ""


def summarize_keywords(processed_text: str, top_n: int = 5):
    """Return top keywords influencing the decision (simple frequency heuristic)."""
    tokens = processed_text.split()
    scores = {}
    for tok in tokens:
        scores[tok] = scores.get(tok, 0) + 1

    ranked = sorted(scores.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [tok for tok, _ in ranked[:top_n]]


def get_confidence_score(news_text):
    """
    Extract confidence score from the model.
    Returns confidence as a percentage (0-100).
    """
    try:
        if loaded_model is None:
            return 50.0
        
        processed_text = preprocess_text(news_text)
        
        if not processed_text:
            return 50.0
        
        input_data = [processed_text]
        
        # Try to get probability scores
        if hasattr(loaded_model, 'named_steps'):
            # It's a pipeline
            clf = loaded_model.named_steps['clf']
            if hasattr(clf, 'predict_proba'):
                proba = loaded_model.named_steps['clf'].predict_proba(input_data)
                # Return the confidence of the predicted class
                confidence = max(proba[0]) * 100
                return round(confidence, 2)
            elif hasattr(clf, 'decision_function'):
                decision = loaded_model.named_steps['clf'].decision_function(input_data)
                # Normalize decision function to 0-100 range
                confidence = (decision[0] + 1) / 2 * 100
                return round(max(0, min(100, confidence)), 2)
        else:
            # Try direct proba method
            if hasattr(loaded_model, 'predict_proba'):
                vectorized = tfidf_v.transform(input_data)
                proba = loaded_model.predict_proba(vectorized)
                confidence = max(proba[0]) * 100
                return round(confidence, 2)
        
        return 50.0
    except Exception as e:
        logger.error(f"Confidence score error: {e}")
        return 50.0


def fake_news_det(news):
    """
    Enhanced fake news detection with keyword-based fallback when model is unavailable.
    """
    try:
        # Validate input
        if not news or len(news.strip()) == 0:
            return {
                'prediction': 'Error: Please enter some news text',
                'confidence': 0,
                'is_error': True
            }
        
        # Check length limit
        if len(news) > MAX_INPUT_LENGTH:
            return {
                'prediction': f'Warning: News text exceeds {MAX_INPUT_LENGTH} characters. Using first {MAX_INPUT_LENGTH} characters.',
                'confidence': 0,
                'is_error': True
            }
        
        # Preprocess text
        processed_text = preprocess_text(news)
        
        if not processed_text:
            return {
                'prediction': 'Error: Invalid text after processing',
                'confidence': 0,
                'is_error': True
            }
        
        input_data = [processed_text]
        
        # If model is available, use it
        if loaded_model is not None:
            # Get confidence score
            confidence = get_confidence_score(news)
            
            # Make prediction
            if hasattr(loaded_model, 'named_steps'):
                prediction = loaded_model.predict(input_data)
            else:
                vectorized_input_data = tfidf_v.transform(input_data)
                prediction = loaded_model.predict(vectorized_input_data)
            
            pred = str(prediction[0]).strip().upper()
            
            if pred in ['0', 'FALSE', 'FAKE']:
                result_text = f"Fake News Detected ({confidence}% confidence)"
                result_type = 'fake'
            else:
                result_text = f"Real News Detected ({confidence}% confidence)"
                result_type = 'real'
            
            return {
                'prediction': result_text,
                'confidence': confidence,
                'type': result_type,
                'is_error': False
            }
        else:
            # Use keyword-based detection when model is not available
            fake_keywords = ['flat earth', 'aliens', 'conspiracy', 'hoax', 'fake', 
                           'mind control', 'lying', 'secret', 'false', 'not real']
            real_keywords = ['research', 'study', 'announce', 'report', 'investigation', 
                            'expert', 'data', 'evidence', 'fact', 'official', 'organization']
            
            text_lower = news.lower()
            fake_score = sum(text_lower.count(kw) for kw in fake_keywords)
            real_score = sum(text_lower.count(kw) for kw in real_keywords)
            
            total = fake_score + real_score
            if total == 0:
                confidence = 50.0
                result_type = 'neutral'
                result_text = "⚠️  Unclear - No specific indicators found (neutral prediction)"
            else:
                fake_percentage = (fake_score / total) * 100
                if fake_percentage > 60:
                    confidence = round(fake_percentage, 2)
                    result_type = 'fake'
                    result_text = f"🚨 Likely Fake News ({confidence}% confidence)"
                else:
                    confidence = round(100 - fake_percentage, 2)
                    result_type = 'real'
                    result_text = f"✓ Likely Real News ({confidence}% confidence)"
            
            return {
                'prediction': result_text,
                'confidence': confidence,
                'type': result_type,
                'is_error': False
            }
    except Exception as e:
        logger.error(f"ERROR in fake_news_det: {str(e)}")
        return {
            'prediction': f'Error during prediction: {str(e)}',
            'confidence': 0,
            'is_error': True
        }


def add_to_history(news_text, result, confidence):
    """
    Add prediction to session history (last 5 results).
    """
    try:
        if 'history' not in session:
            session['history'] = []
        
        history = session['history']
        history.insert(0, {
            'text': news_text[:100],  # Store first 100 chars
            'result': result,
            'confidence': confidence,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Keep only last 5
        session['history'] = history[:5]
        session.modified = True
    except Exception as e:
        logger.error(f"Error adding to history: {e}")


@app.route('/')
def home():
    """Render home page with prediction history."""
    history = session.get('history', [])
    return render_template('index.html', history=history)


@app.route('/index.html')
def index_html():
    """Support direct /index.html requests."""
    return redirect(url_for('home'))


@app.route('/favicon.ico')
def favicon():
    """Prevent 404s for favicon."""
    return Response(status=204)


@app.route('/predict', methods=['POST'])
def predict():
    """
    Enhanced prediction route with POST-Redirect-GET pattern.
    """
    try:
        if request.method == 'POST':
            # Validate form data
            if 'news' not in request.form:
                logger.error("'news' key not found in form data")
                return render_template('index.html', 
                                     prediction_error="Error: No news text provided",
                                     history=session.get('history', []))
            
            news_text = request.form['news'].strip()
            
            # Validate input
            if not news_text:
                return render_template('index.html',
                                     prediction_error="Error: Please enter some news text",
                                     history=session.get('history', []))
            
            if len(news_text) > MAX_INPUT_LENGTH:
                news_text = news_text[:MAX_INPUT_LENGTH]
            
            logger.info(f"Processing news: {news_text[:100]}...")
            
            # Get prediction with timing
            start_time = time.time()
            result = fake_news_det(news_text)
            processing_time = round(time.time() - start_time, 3)
            
            # Add to history if successful
            if not result.get('is_error'):
                add_to_history(news_text, result['prediction'], result['confidence'])
            
            return render_template('index.html',
                                 prediction=result['prediction'],
                                 confidence=result.get('confidence', 0),
                                 result_type=result.get('type', 'neutral'),
                                 is_error=result.get('is_error', False),
                                 processing_time=f"{processing_time}s",
                                 history=session.get('history', []))
    except Exception as e:
        logger.error(f"Error in predict route: {str(e)}")
        return render_template('index.html',
                             prediction_error=f"Server error: {str(e)}",
                             history=session.get('history', []))


@app.route('/api/sample', methods=['GET'])
def get_sample_news():
    """
    API endpoint to get sample news for testing.
    """
    try:
        sample_type = request.args.get('type', 'fake')
        
        if sample_type == 'real':
            return jsonify({
                'success': True,
                'news': SAMPLE_NEWS_REAL,
                'type': 'real'
            })
        else:
            return jsonify({
                'success': True,
                'news': SAMPLE_NEWS_FAKE,
                'type': 'fake'
            })
    except Exception as e:
        logger.error(f"Error in get_sample_news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    API endpoint to get prediction history.
    """
    try:
        history = session.get('history', [])
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        logger.error(f"Error in get_history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/social-verify', methods=['POST'])
def social_verify():
    """Instant verification for social media/text/URLs using existing model."""
    try:
        data = request.get_json(silent=True) or {}
        platform = (data.get('platform') or 'news').strip().lower()
        content = (data.get('content') or '').strip()

        if not content:
            return jsonify({
                'success': False,
                'error': 'Please provide text or a URL to verify.'
            }), 400

        # If a URL is provided, fetch and extract text
        text_to_analyze = content
        if platform == 'news url' or is_url(content):
            fetched = extract_text_from_url(content)
            if not fetched:
                return jsonify({
                    'success': False,
                    'error': 'Unable to fetch content from the provided URL.'
                }), 400
            text_to_analyze = fetched

        if len(text_to_analyze) > MAX_INPUT_LENGTH:
            text_to_analyze = text_to_analyze[:MAX_INPUT_LENGTH]

        start_time = time.time()
        result = fake_news_det(text_to_analyze)
        processing_time = round(time.time() - start_time, 3)

        processed = preprocess_text(text_to_analyze)
        reasons = summarize_keywords(processed) if processed else []

        status_code = 200 if not result.get('is_error') else 500

        return jsonify({
            'success': not result.get('is_error'),
            'label': result.get('type', 'neutral'),
            'prediction': result.get('prediction'),
            'confidence': result.get('confidence', 0),
            'reason_summary': ', '.join(reasons) if reasons else 'Key indicators identified from input text.',
            'reasons': reasons,
            'processing_time': f"{processing_time}s",
            'platform': platform
        }), status_code
    except Exception as e:
        logger.error(f"Error in social_verify: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """
    API endpoint to clear prediction history.
    """
    try:
        session['history'] = []
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'History cleared'
        })
    except Exception as e:
        logger.error(f"Error in clear_history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)