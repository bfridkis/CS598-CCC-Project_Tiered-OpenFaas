# Use the official Alpine Linux image as the base
FROM alpine:3

WORKDIR /.

# Copy the amazon-reviews test data set (compressed), pre-trained model, and vectorizer
COPY /datasets/amazon-reviews/amazon-reviews-test.ft.txt.bz2 datasets/amazon-reviews/amazon-reviews-test.ft.txt.bz2
COPY /models/tfidf_vectorize_amazon-reviews/tfidf_vectorize_model_amazon-reviews.joblib models/tfidf_vectorize_amazon-reviews/tfidf_vectorize_model_amazon-reviews.joblib
COPY /vectorizers/tfidf_vectorize_amazon-reviews/tfidf_vectorize_vectorizers_amazon-reviews.joblib vectorizers/tfidf_vectorize_amazon-reviews/tfidf_vectorize_vectorizers_amazon-reviews.joblib

# Copy the sms-spam test data set (compressed), pre-trained model, and vectorizer
COPY /datasets/sms-spam/SMSSpamCollection_Test datasets/sms-spam/SMSSpamCollection_Test
COPY /models/tfidf_vectorize_sms-spam/tfidf_vectorize_model_sms-spam.joblib models/tfidf_vectorize_sms-spam/tfidf_vectorize_model_sms-spam.joblib
COPY /vectorizers/tfidf_vectorize_sms-spam/tfidf_vectorize_vectorizers_sms-spam.joblib vectorizers/tfidf_vectorize_sms-spam/tfidf_vectorize_vectorizers_sms-spam.joblib