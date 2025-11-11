import joblib
import pandas as pd
import numpy as np
import os
# import kagglehub

# Partially AI Generated: https://www.google.com/search?q=in+the+following+code+why+does+it+need+a+model_path+import+pandas+as+pd+import+joblib+from+sklearn.feature_extraction.text+import+TfidfVectorizer+import+os+from+time+import+time+%23+Assuming+%27cleanup%27+and+%27s3_client%27+are+defined+elsewhere+in+your+function+def+lambda_handler%28event%2C+context%29%3A+x+%3D+event%5B%27x%27%5D+model_path+%3D+%27%2Ftmp%2F%27+%2B+event%5B%27model_object_key%27%5D+%23+Use+%2Ftmp+directory+%23+---+Dataset+Loading+---+%23+The+dataset+is+bundled+locally+in+the+%27app%27+directory+dataset_path+%3D+%27app%2FSMSSpamCollection.tsv%27+%23+Read+as+TSV+%28sep%3D%27%5Ct%27%29+and+manually+assign+column+names+to+match+expected+%27Text%27+dataset+%3D+pd.read_csv%28dataset_path%2C+sep%3D%27%5Ct%27%2C+header%3DNone%2C+names%3D%5B%27Label%27%2C+%27Text%27%5D%29+start+%3D+time%28%29+df_input+%3D+pd.DataFrame%28%29+df_input%5B%27x%27%5D+%3D+%5Bx%5D+df_input%5B%27x%27%5D+%3D+df_input%5B%27x%27%5D.apply%28cleanup%29+dataset%5B%27train%27%5D+%3D+dataset%5B%27Text%27%5D.apply%28cleanup%29+tfidf_vect+%3D+TfidfVectorizer%28min_df%3D100%29.fit%28dataset%5B%27train%27%5D%29+X+%3D+tfidf_vect.transform%28df_input%5B%27x%27%5D%29+%23+---+Model+Loading+%28as+in+original+code%29+---+%23+Ensure+the+model+file+is+downloaded+to+%2Ftmp+first+if+not+os.path.isfile%28model_path%29%3A+s3_client.download_file%28event%5B%27model_bucket%27%5D%2C+event%5B%27model_object_key%27%5D%2C+model_path%29+model+%3D+joblib.load%28model_path%29+y+%3D+model.predict%28X%29+latency+%3D+time%28%29+-+start+return+%7B%27y%27%3A+y.tolist%28%29%2C+%27latency%27%3A+latency%7D+%23+Convert+numpy+array+%27y%27+to+a+list+for+JSON+serialization&sca_esv=8d68d2504fc7931b&rlz=1C1CHBF_enUS1071US1071&udm=50&fbs=AIIjpHxU7SXXniUZfeShr2fp4giZ1Y6MJ25_tmWITc7uy4KIeioyp3OhN11EY0n5qfq-zENwnGygERInUV_0g0XKeHGJEwefEKJ1XNp8V3tgIFOgMDy0Fj0iCOgjQP-IlptzEz6QeQCzj8Gmr06Dlj_CyjNItrcH5arx6u7qFDs7lYIjliS_gBRNYBPRR89PKIiM_EJZUU5qnI5sFylN4cV10iWTeS4A1g&aep=1&ntc=1&sa=X&ved=2ahUKEwjSxJCsmtyQAxX_kWoFHRtqBdMQ2J8OegQICxAE&biw=2880&bih=1366&dpr=0.67&mstk=AUtExfCj5Z5J8sL7MqfHU35B5MlhPcGEMfre9Hg7FCtRS-4FrMEVW2UwmtgiYuOklKhuZCNcOyzUXxNI6N4zvb2v0RIdvcpl1C8k0rjaqn7XsNMCCW6xANMu4izliF0p85hG0zH-1WRNOMjzJ_t1I-RweQyD4UCXqIhBtUvnVW_THueo3vTLT1tLwsDqGX6QOXOlsxYrlg2pqLC2-69xr9skG8D6rbEzm-TzGV-a4uUgk-FrHOOP56dDtEP_QQ&csuir=1

def read_kaggle_text_file(file_path, dataset):
    """
    Reads a fastText-formatted text file into a pandas DataFrame 
    with 'label' and 'message' columns.
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}. Please check your path.")

    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Strip leading/trailing whitespace
            line = line.strip()
            if not line:
                continue # Skip blank lines

            # Find the index of the first space
            first_space_index = line.find(' ')
            
            if first_space_index == -1:
                # Handle lines with no space (unlikely in this dataset)
                continue

            # Extract the label (e.g., '__label__1')
            label_raw = line[:first_space_index]
            
            # Extract the message (the rest of the line after the first space)
            message = line[first_space_index + 1:].strip()
            
            data.append({'label_raw': label_raw, 'message': message})

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(data)
    
    # Optional: Convert the raw label string into an integer (1 or 0)
    # This might be necessary depending on how your model was trained
    if dataset == 'amazon-reviews':
        df['label'] = df['label_raw'].apply(lambda x: 1 if '__label__2' in x else 0)
    else:
        df['label'] = df['label_raw'].apply(lambda x: 1 if 'ham' in x else 0)
    
    return df

def handle(event, context):
    
    try:
        dataset = event.headers.get('X-Dataset')
        if not (dataset == 'amazon-reviews' or dataset == 'sms-spam'):
            print(f"Invalid 'X-Dataset' header value '{X-Dataset}'. (Must be 'amazon-reviews' or 'sms-spam'.) Using 'sms-spam'...")
            dataset = 'sms-spam'
    except Exception as e:
        print(f"Exception {e}. Invalid or missing 'X-Dataset' header. Using 'sms-spam'...")
        dataset = 'sms-spam'
    
    print("Starting tfidf-vectorize...")
    
    dataset_path = f'/data/datasets/{dataset}/{'SMSSpamCollection_Test' if dataset == 'sms-spam' else 'amazon-reviews-test.ft.txt'}'
    model_path = f'/data/models/tfidf_vectorize_{dataset}/tfidf_vectorize_model_{dataset}.joblib'
    vectorizer_path = f'/data/vectorizers/tfidf_vectorize_{dataset}/tfidf_vectorize_vectorizers_{dataset}.joblib'

    # Load the trained model and vectorizer
    if not os.path.exists(model_path) or not os.path.exists(vectorizer_path) or not os.path.exists(dataset_path):
        print("Model or vectorizer or dataset files not found.")
        { 
            "statusCode": 299,
            "body": "Model or vectorizer or dataset files not found."        
    }

    model = joblib.load(model_path)
    print(f"Finished loading model from {model_path}...")
    tfidf_vectorizer = joblib.load(vectorizer_path)
    print(f"Finished loading vectorizers from {vectorizer_path}...")

    # --- Another Publicly Available Data Set / New Data ---
    # Example: A list of new messages to classify
    # reviews_for_inference = [
        # "Congratulations! You've won a free holiday for two. Call now!",
        # "Hey, are we still on for dinner tonight?",
        # "URGENT: Your account has been compromised. Log in immediately via the link provided.",
        # "Thanks for the update, that sounds good.",
        # "Get rich quick with our amazing new scheme. Sign up today!",
        # "I will be late for the meeting, stuck in traffic.",
        # "Your Amazon parcel is waiting for delivery. Please confirm your details here: [link]",
    # ]
    
    reviews_for_inference = read_kaggle_text_file(dataset_path, dataset)
    print(f"Finished loading dataset from {dataset_path}...")
    labels = reviews_for_inference['label']

    # Transform the new data using the *previously fitted* vectorizer
    # Do NOT call .fit_transform() here; only .transform() is correct for new data.
    X_new_transformed = tfidf_vectorizer.transform(reviews_for_inference['message'])
    print(f"Finished transforming data using vectorizer...")

    # Make predictions
    predictions = model.predict(X_new_transformed)
    print(f"Finished making predictions...")
    
    # Calculate accuracy
    accuracy = np.mean(predictions == labels)
    
    if dataset == 'amazon-reviews':
        body_string = f"tfidf_vectorize complete. Accuracy: {accuracy}. Predicted vs. Actual -- 4-5 Star Review Count: {np.sum(predictions == 1)} vs. {np.sum(labels == 1)} | 1-2 Star Review Count: {np.sum(predictions == 0)} vs. {np.sum(labels == 0)}"
    else:
        body_string = f"tfidf_vectorize complete. Accuracy: {accuracy}. Predicted vs. Actual -- ham Count: {np.sum(predictions == 1)} vs. {np.sum(labels == 1)} | spam Count: {np.sum(predictions == 0)} vs. {np.sum(labels == 0)}"
    
    print(body_string)
    
    return { 
        "statusCode": 200,
        # predictions: predictions.tolist()
        "body": body_string        
    }
    
# Reference 
# https://github.com/ddps-lab/serverless-faas-workbench/blob/master/aws/cpu-memory/model_serving/ml_lr_prediction/lambda_function.py

# Reference for Amazon Reviews dataset
# https://www.kaggle.com/datasets/bittlingmayer/amazonreviews

#Reference for dataset (BibTeX) - SMS Spam
# @misc{sms_spam_collection_228,
  # author       = {Almeida, Tiago and Hidalgo, Jos},
  # title        = {{SMS Spam Collection}},
  # year         = {2011},
  # howpublished = {UCI Machine Learning Repository},
  # note         = {{DOI}: https://doi.org/10.24432/C5CC84}
#}