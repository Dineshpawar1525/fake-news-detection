#!/usr/bin/env python3
"""
Retrain the fake news detection model with current sklearn version.
This replaces the old incompatible model.pkl with a new one.

Usage:
    python retrain_model.py
"""
import pandas as pd
import pickle
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*60)
print("RETRAINING MODEL.PKL WITH CURRENT SKLEARN VERSION")
print("="*60 + "\n")

try:
    # Load training data
    logger.info("📂 Loading train.csv...")
    df = pd.read_csv('train.csv')
    X = df['Statement'].astype(str)
    y = df['Label'].astype(str)
    
    logger.info(f"✓ Training data loaded: {len(df)} samples")
    logger.info(f"  Labels distribution: {y.value_counts().to_dict()}\n")
    
    # Create and train pipeline with current sklearn
    logger.info("🤖 Training model...")
    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000, min_df=1, max_df=0.9)),
        ('clf', SGDClassifier(loss='hinge', random_state=42, max_iter=1000, n_jobs=-1, verbose=0))
    ])
    
    pipe.fit(X, y)
    logger.info("✓ Model trained successfully\n")
    
    # Save the model
    logger.info("💾 Saving model to model.pkl...")
    with open('model.pkl', 'wb') as f:
        pickle.dump(pipe, f)
    logger.info("✓ Model saved\n")
    
    # Test predictions
    logger.info("🧪 Testing predictions:")
    test_cases = [
        "The President announced today that the Earth is flat and space doesn't exist",
        "The World Health Organization announced new guidelines for public health management",
        "Aliens have invaded the White House",
        "Scientists publish new findings on renewable energy"
    ]
    
    for text in test_cases:
        pred = pipe.predict([text])
        confidence = pipe.decision_function([text])[0]
        logger.info(f"\n  Text: {text[:60]}...")
        logger.info(f"  Prediction: {pred[0]} | Confidence: {confidence:.2f}")
    
    print("\n" + "="*60)
    logger.info("✅ MODEL RETRAINING COMPLETE!")
    print("="*60 + "\n")
    
except FileNotFoundError as e:
    logger.error(f"✗ Error: train.csv not found! {e}")
    print("="*60 + "\n")
except Exception as e:
    logger.error(f"✗ Error during training: {e}")
    import traceback
    traceback.print_exc()
    print("="*60 + "\n")
