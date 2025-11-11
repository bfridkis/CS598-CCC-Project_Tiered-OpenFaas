import time
import json
import random
#import logging


# logging.basicConfig(
    # level=logging.DEBUG,
    # format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
# )

# Get a logger instance for the current module
# Using __name__ is a common convention
#logger = logging.getLogger(__name__)

# Importing a large, heavy library here will significantly increase container load time.
# The import happens in the global scope, during the container's cold start.
#print("Beginning heavy library import. This will take time during cold start.")
#from sklearn.ensemble import RandomForestClassifier
#print("Heavy library import finished.")

# Global variables are initialized during container startup.
# This simulates a common scenario where a model is loaded once per container instance.
#print("Loading a pre-trained model. This also adds to cold start time.")
#model = RandomForestClassifier()
# Replace this with your actual model loading logic.

# Global sleep only runs during container initialization, so simulates load time accordingly.
#logger.info(f"Global Sleeping Starting...")
print(f"Global Sleep Starting...")
time.sleep(5)
#logger.info(f"Global Sleeping Completed")
print(f"Global Sleep Completed")

def handle(event, context):
    #logger.info(f"headers: {event.headers}")
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
    #logger.info(f"body: {event.body}")
    try:
        print(f"body: {json.loads(event.body)}")
    except:
        pass
    #logger.info(f"Sleeping Now...")
    print("Sleeping now...")
    try:
        sleep_time = int(event.headers.get('Compute-Time'))
        #sleep_time = int(json.loads(event.body)['compute-time'])
        assignment_method = "Duration specified via 'compute-time' field passed in invocation body."
    except:
        sleep_time = random.randint(0, 20)
        assignment_method = "Randomly assigned duration."
    time.sleep(sleep_time)
    #logger.info(f"Done Sleeping...")
    print(f"Done sleeping. Sleep was for {sleep_time} seconds. {assignment_method}")
    
    try:
        body_string = f"Hello from OpenFaaS sleep {event.headers.get('X-Tier')} tier! Slept for {sleep_time} seconds."
    except:
        body_string = f"Hello from OpenFaaS sleep! Slept for {sleep_time} seconds."
    
    return {
        "statusCode": 200,
        "body": body_string
    }
