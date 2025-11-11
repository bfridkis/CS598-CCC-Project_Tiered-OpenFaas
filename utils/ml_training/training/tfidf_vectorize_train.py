import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
import os
import requests
import io
from utils.read_kaggle_text_file import read_kaggle_text_file

# AI Generated: https://www.google.com/search?q=in+the+following+code+why+does+it+need+a+model_path+import+pandas+as+pd+import+joblib+from+sklearn.feature_extraction.text+import+TfidfVectorizer+import+os+from+time+import+time+%23+Assuming+%27cleanup%27+and+%27s3_client%27+are+defined+elsewhere+in+your+function+def+lambda_handler%28event%2C+context%29%3A+x+%3D+event%5B%27x%27%5D+model_path+%3D+%27%2Ftmp%2F%27+%2B+event%5B%27model_object_key%27%5D+%23+Use+%2Ftmp+directory+%23+---+Dataset+Loading+---+%23+The+dataset+is+bundled+locally+in+the+%27app%27+directory+dataset_path+%3D+%27app%2FSMSSpamCollection.tsv%27+%23+Read+as+TSV+%28sep%3D%27%5Ct%27%29+and+manually+assign+column+names+to+match+expected+%27Text%27+dataset+%3D+pd.read_csv%28dataset_path%2C+sep%3D%27%5Ct%27%2C+header%3DNone%2C+names%3D%5B%27Label%27%2C+%27Text%27%5D%29+start+%3D+time%28%29+df_input+%3D+pd.DataFrame%28%29+df_input%5B%27x%27%5D+%3D+%5Bx%5D+df_input%5B%27x%27%5D+%3D+df_input%5B%27x%27%5D.apply%28cleanup%29+dataset%5B%27train%27%5D+%3D+dataset%5B%27Text%27%5D.apply%28cleanup%29+tfidf_vect+%3D+TfidfVectorizer%28min_df%3D100%29.fit%28dataset%5B%27train%27%5D%29+X+%3D+tfidf_vect.transform%28df_input%5B%27x%27%5D%29+%23+---+Model+Loading+%28as+in+original+code%29+---+%23+Ensure+the+model+file+is+downloaded+to+%2Ftmp+first+if+not+os.path.isfile%28model_path%29%3A+s3_client.download_file%28event%5B%27model_bucket%27%5D%2C+event%5B%27model_object_key%27%5D%2C+model_path%29+model+%3D+joblib.load%28model_path%29+y+%3D+model.predict%28X%29+latency+%3D+time%28%29+-+start+return+%7B%27y%27%3A+y.tolist%28%29%2C+%27latency%27%3A+latency%7D+%23+Convert+numpy+array+%27y%27+to+a+list+for+JSON+serialization&sca_esv=8d68d2504fc7931b&rlz=1C1CHBF_enUS1071US1071&udm=50&fbs=AIIjpHxU7SXXniUZfeShr2fp4giZ1Y6MJ25_tmWITc7uy4KIeioyp3OhN11EY0n5qfq-zENwnGygERInUV_0g0XKeHGJEwefEKJ1XNp8V3tgIFOgMDy0Fj0iCOgjQP-IlptzEz6QeQCzj8Gmr06Dlj_CyjNItrcH5arx6u7qFDs7lYIjliS_gBRNYBPRR89PKIiM_EJZUU5qnI5sFylN4cV10iWTeS4A1g&aep=1&ntc=1&sa=X&ved=2ahUKEwjSxJCsmtyQAxX_kWoFHRtqBdMQ2J8OegQICxAE&biw=2880&bih=1366&dpr=0.67&mstk=AUtExfBxRu7EFJ9QNjS72SpvvI5e_B0pkBWQ0qHgv4B085tLVpQRBpwBf7sziw1spLJIj9DBJ-EA-uHsWGhgd6Eq_YWb0B99juoyPjrDvioyqmFKPRK5O7uX4LAAZsvNZOF7bGeObJhFmUHT35NKLOtx3oAvMnEgPn5KnFJ6BTk6E1YlUK4mEr0SYJUi1MCRuexpuPD83BaWZmsyficpC-5w1KX0VOUiL84fuzHoKoc5A8wNWy8uY-vlwFV-tg&csuir=1

def tfidf_vectorize_train(training_dataset = r"C:\Users\Annjamin\Documents\Benj's Stuff\UIUC MCS\CS598-CloudComputingCapstone\Project\ReposForProject\OpenFaaS-SLO-Tiering-Per-Invocation-Team6\utils\ml_training\datasets\sms-spam\SMSSpamCollection_Train", 
                          model_path = r"C:\Users\Annjamin\Documents\Benj's Stuff\UIUC MCS\CS598-CloudComputingCapstone\Project\ReposForProject\OpenFaaS-SLO-Tiering-Per-Invocation-Team6\utils\ml_training\models\tfidf_vectorize_sms-spam\tfidf_vectorize_model_sms-spam.joblib", 
                          vectorizer_path = r"C:\Users\Annjamin\Documents\Benj's Stuff\UIUC MCS\CS598-CloudComputingCapstone\Project\ReposForProject\OpenFaaS-SLO-Tiering-Per-Invocation-Team6\utils\ml_training\vectorizers\tfidf_vectorize_vectorizers-sms-spam.joblib"):

    
    data = read_kaggle_text_file(training_dataset)
    
    # Split data into training and testing sets
    # We will use the 'test' set here for *training* the model which we'll then apply to *new* data later
    X_train, X_test, y_train, y_test = train_test_split(
        data['message'], data['label'], test_size=0.2, random_state=42
    )

    # Initialize and fit the TfidfVectorizer on training data
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    X_train_transformed = tfidf_vectorizer.fit_transform(X_train)
    X_test_transformed = tfidf_vectorizer.transform(X_test) # Only transform test data

    # Train a classifier
    model = MultinomialNB()
    model.fit(X_train_transformed, y_train)

    # Save the trained model and the fitted vectorizer
    joblib.dump(model, model_path)
    joblib.dump(tfidf_vectorizer, vectorizer_path)

    print(f"Model saved to {model_path}")
    print(f"Vectorizer saved to {vectorizer_path}")

if __name__ == "__main__":
    tfidf_vectorize_train()

# Reference - Dataset Source
# https://www.kaggle.com/datasets/bittlingmayer/amazonreviews