import sys

from sqlalchemy import create_engine
import nltk
nltk.download(['punkt', 'wordnet'])
import re
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.multioutput import MultiOutputClassifier
import pickle

def load_data(database_filepath):
    """
    INPUT:
    database_filepath - path to database to be loaded

    OUTPUT:
    X - messages (input variable)
    y - categories of the messages (output variable)
    category_names - category name for y
    """
    engine = create_engine('sqlite:///'+database_filepath)
    df = pd.read_sql_table('DisasterResponse', engine)
    X = df.message
    y = df[df.columns[4:]]
    category_names = y.columns
    return X, y, category_names


def tokenize(text):
    """
    INPUT:
    text - raw text

    OUTPUT:
    clean_tokens - tokenized messages
    """
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    detected_urls = re.findall(url_regex, text)
    for url in detected_urls:
        text = text.replace(url, "urlplaceholder")

    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model():
    """
    INPUT:
    None

    OUTPUT:
    cv = ML model pipeline after performing grid search
    """
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier()))
    ])
    parameters = {'vect__ngram_range': ((1, 1), (1, 2))
        , 'vect__max_df': (0.5, 0.75)
        , 'tfidf__use_idf': (True, False)
        , 'clf__estimator__n_estimators': [100, 200]
        , 'clf__estimator__min_samples_split': [2,  4]
    }
    cv = GridSearchCV(pipeline, param_grid=parameters, n_jobs=-1, verbose=2, cv=3)
    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    """
    INPUT:
    model - ML model
    X_test - test messages
    y_test - categories for test messages
    category_names - category name for y

    OUTPUT:
    none - print scores (precision, recall, f1-score) for each output category of the dataset.
    """
    y_pred = model.predict(X_test)
    class_report = classification_report(Y_test, y_pred, target_names=category_names)
    print(class_report)


def save_model(model, model_filepath):
    """
    INPUT:
    model - ML model
    model_filepath - location to save the model

    OUTPUT:
    none
    """
    with open(model_filepath, 'wb') as file:
        pickle.dump(model, file)


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()