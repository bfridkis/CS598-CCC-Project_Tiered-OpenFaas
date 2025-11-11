import sys
import requests
import random
import json
import time
import datetime
import concurrent.futures

## Dict to contain test parameters from JSON
functions = {}
tiers = {}

execMode = 'naive'
execCount = 0
execLimit = 1000

filename = 'Moby.txt'

request_list = []

## Set endpoint target (updated for macOS/OpenFaaS) change as necessary.
baseURL = "http://127.0.0.1:5055/invoke/"
# baseURL = 'http://example.com/curl'

## Load function parametes from JSON file
try:
    with open('functions.json', 'r') as f:
        functions = json.load(f)
except FileNotFoundError:
    print("Error: 'functions.json' - file not found.")
except json.JSONDecodeError:
    print("Error: 'functions.json' - improper json.")

try:
    with open('tiers.json', 'r') as t:
        tiers = json.load(t)
except FileNotFoundError:
    print("Error: 'tiers.json' - file not found.")
except json.JSONDecodeError:
    print("Error: 'tiers.json' - improper json.")

def main(mode = 'naive', **kwargs):
    execMode = mode
    arguments = parseArguments(**kwargs)

    rounds = arguments["rounds"]
    wait = arguments["wait"]
    seconds = arguments["seconds"]
    lx = arguments["lx"]
    mx = arguments["mx"]
    hx = arguments["hx"]
    exp = arguments["exp"]
    pause = arguments["pause"]

    if execMode == 'naive':
        naive()
    elif execMode == 'round':
        roundRobin(wait, rounds, seconds, pause)
    elif execMode in ('burst', 'ramp', 'exp'):
        dynamicRequest(mode, rounds, wait, seconds, lx, mx, hx, exp, pause)
    else:
        naive()

## Parse Args
def parseArguments(**kwargs):
    #Inatakes args and ensures proper defaults.

    # wait      = iterations/second
    # pause     = time to pause between execution rounds
    # rounds    = rounds of invocation to make
    # seconds   = seconds to run before executions stops
    # mx        = mid multiplier
    # hx        = high multiplier
    # lx        = low multipier
    # exp    = exponential scaling multiplier

    arguments = kwargs.copy()

    # Set defaults for kwargs
    arguments.setdefault('wait', 0)
    arguments.setdefault('pause', 0)        
    arguments.setdefault('rounds', 1)
    arguments.setdefault('seconds', 0)
    arguments.setdefault('exp', 1)
    arguments.setdefault('mx', 1)
    arguments.setdefault('hx', 1)
    arguments.setdefault('lx', 1)
    
    for key in arguments:
        arguments[key] = int(float(arguments[key]))

    return arguments    

## Get wait interval for iterations/second requests
def waitInterval(wait):
    ## default to 0 for i <= 0
    if wait <= 0:
        return 0
    
    ## Ensure returned wait will be >= 0
    sleepInterval = wait

    if sleepInterval <= 0:
        return 0
    else:
        return sleepInterval

# Build and send a request
def requsetBuilder(function, tier):
    # Use the router endpoint
    url = baseURL + function

    headers = {}
    headers[functions[function]["headers"]["computeTime"]] = functions[function]["computeSeconds"]
    headers[functions[function]["headers"]["xTier"]] = tier

    
    if function == 'word_count':
        data = get_words(filename)
    else:
        data = functions[function]["body"]

    req = {}

    req['url'] = url
    req['headers'] = headers
    req['data'] = data
    req['timeout'] = 30
    req['tier'] = tier
    req['function'] = function

    request_list.append(req)

# Send the requests 
def request_send():

    # randomize request order
    random.shuffle(request_list)

    for req in request_list:
        url = req['url']
        headers = req['headers']
        data = req['data']
        to = req['timeout']
        tier = req['tier']
        function = req['function']

        try:
            # Send data directly, requests will handle JSON encoding
            response = requests.post(url, headers=headers, json=data, timeout=to)
            print(f"{function}-{tier} Status Code:", response.status_code)

        except requests.exceptions.RequestException as e:
            print(f"{function}-{tier} Error:", str(e))        

    request_list.clear()

    # try:
    #     # Send data directly, requests will handle JSON encoding
    #     response = requests.post(url, headers=headers, json=data, timeout=30)
    #     print(f"{function}-{tier} Status Code:", response.status_code)
    # except requests.exceptions.RequestException as e:
    #     print(f"{function}-{tier} Error:", str(e))

def get_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        return text

## Naive request
    ## Mostly for testing
    ## Will run each function one time/tier
def naive():

    print(f'Running naive execution, all functions once per tier.')

    for function in functions.keys():
        for tier in tiers.keys():

            requsetBuilder(function, tier)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(request_send(), range(3))

    print("Execution finished.")


## Construct round robin test delivery
    ## Invoke functions once per tier sequentially
    ## Continue by requests/second until time out OR discrete number of rounds
def roundRobin(wait, rounds, seconds, pause):

    roundCount = 0
    duration = seconds

    waitSeconds = waitInterval(wait)

    if duration == 0:

        ## Run for specified number of cycles
        print(f'Running Round Robin test for: {rounds} rounds.')

        while roundCount < rounds:
            for function in functions.keys():
                for tier in tiers.keys():

                    requsetBuilder(function, tier)

                    # time.sleep(waitSeconds)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(request_send(), range(3)) 

            roundCount += 1

            time.sleep(pause)


        print("Execution finished.")

    else:
        ## Run for specified number of seconds, wait optional, default is 0 wait. 
        endTime = datetime.datetime.now() + datetime.timedelta(seconds = duration)

        if waitSeconds == 0: 

            print(f'Running Round Robin test for: {duration} seconds, at constant wait.')

        else:

            print(f'Running Round Robin test for: {duration} seconds, at {wait} invocations/second.')

        while datetime.datetime.now() < endTime:
            for function in functions.keys():
                for tier in tiers.keys():

                    requsetBuilder(function, tier)

                    # time.sleep(waitSeconds)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(request_send(), range(3)) 

        print("Execution finished.")

# Execute requests in Burst, Ramp, or Exponential pattern
def dynamicRequest(mode, rounds, wait, seconds, lx, mx, hx, exp, pause):

    global execLimit
    global execCount

    roundCount = 0
    duration = seconds

    h_target = hx
    m_target = mx
    l_target = lx

    lx_count = 0
    mx_count = 0
    hx_count = 0

    waitSeconds = waitInterval(wait)

    if duration == 0:

        ## Run for specified number of cycles
        print(f'Running {mode} test for: {rounds} rounds. H:{hx}  M:{mx}  L:{lx} per round.')

        while roundCount < rounds:
            for function in functions:
                for tier in tiers.keys():

                    if tier in ("high", "hi", "h"):

                        while hx_count < h_target:

                            requsetBuilder(function, tier)
                            hx_count += 1
                            # time.sleep(waitSeconds)

                    elif tier in ("medium", "med", "m"):

                        while mx_count < m_target:

                            requsetBuilder(function, tier)
                            mx_count += 1
                            # time.sleep(waitSeconds)

                    elif tier in ("low", "lo", "l"):
                        while lx_count < l_target:

                            requsetBuilder(function, tier)
                            lx_count += 1
                            # time.sleep(waitSeconds)

                hx_count = 0
                mx_count = 0
                lx_count = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(request_send(), range(3))

            roundCount += 1  

            time.sleep(pause)     

        print("Execution finished.")

    else:
        ## Run for specified number of seconds, wait/sec optional, default is 0 wait. 
        endTime = datetime.datetime.now() + datetime.timedelta(seconds = duration)

        if waitSeconds == 0: 

            print(f'Running {mode} test for: {duration} seconds, at constant wait. H:{hx}  M:{mx}  L:{lx} per round.')

        else:

            print(f'Running {mode} test for: {duration} seconds, at {wait} invocations/second. H:{hx}  M:{mx}  L:{lx} per round.')

        while datetime.datetime.now() < endTime:
            for function in functions:
                for tier in tiers.keys():

                    if tier in ("high", "hi", "h"):

                        while hx_count < h_target and datetime.datetime.now() < endTime:

                            requsetBuilder(function, tier)
                            hx_count += 1
                            # time.sleep(waitSeconds)

                    elif tier in ("medium", "med", "m"):

                        while mx_count < m_target and datetime.datetime.now() < endTime:

                            requsetBuilder(function, tier)
                            mx_count += 1
                            # time.sleep(waitSeconds)

                    elif tier in ("low", "lo", "l") and datetime.datetime.now() < endTime:
                        while lx_count < l_target:
                            
                            requsetBuilder(function, tier)
                            lx_count += 1
                            # time.sleep(waitSeconds)

                # Reset counts for next round
                hx_count = 0
                mx_count = 0
                lx_count = 0

                # If ramp, scale linearly
                if mode == 'ramp':
                    h_target += hx
                    m_target += mx
                    l_target += lx

                # If exp scale exponentially
                if mode == 'exp':
                    h_target = hx * (1 + exp) ** roundCount
                    m_target = mx * (1 + exp) ** roundCount
                    l_target = lx * (1 + exp) ** roundCount                

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(request_send(), range(3)) 

            roundCount += 1  

            time.sleep(pause)
            
        print("Execution finished.")

if __name__ == "__main__":
    main(sys.argv[1],
         **dict(arg.split('=') for arg in sys.argv[2:]))
