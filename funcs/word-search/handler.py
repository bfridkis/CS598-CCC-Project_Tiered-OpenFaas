import json

def count_words(text):
    words = text.split()
    return len(words)

def handle(event, context):
    try:
        print(f"Compute-Time: {event.headers.get('Compute-Time')}")
    except:
        pass
    try:
        print(f"X-Start-Time: {event.headers.get('X-Start-Time')}")
    except:
        pass
    try:
        print(f"X-Call-Id: {event.headers.get('X-Call-Id')}")
    except:
        pass
    try:
        print(f"body: {json.loads(event.body)}")
    except:
        pass
           
    result = count_words(json.loads(event.body))
    
    print(f"Done with Word Count: {result:.2e}")
    
    return {
        "statusCode": 200,
        "body": f"Hello from OpenFaaS high tier! CPU work completed: {result:.2e}"
    }
