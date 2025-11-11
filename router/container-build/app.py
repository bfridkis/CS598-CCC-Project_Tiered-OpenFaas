from flask import Flask, request, jsonify
import requests, time, csv
from datetime import datetime
from utils.create_results_csv import create_results_csv
# from utils.get_openfaas_basic_auth_pwd import get_openfaas_basic_auth_pwd    # Use if authentication needed, but not required by default. See utils/get_openfaas_basic_auth_pwd.py, make sure to add additional modules to requirements.txt for docker image build
GATEWAY="http://gateway.openfaas:8080"
# USER = 'admin' ; PASS = get_openfaas_basic_auth_pwd()    # Use if authentication needed, but not required by default. See utils/get_openfaas_basic_auth_pwd.py, make sure to add additional modules to requirements.txt for docker image build
X_CALLBACK_ID="http://openfaas-preprocessor-service.openfaas-tiering:80/callback"
REQUEST_OUTPUT_FILE = create_results_csv(filename=f"request-results_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv", kind="request")
CALLBACK_OUTPUT_FILE = create_results_csv(filename=f"callback-results_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv", kind="callback")

app=Flask(__name__)

# Store invoke times keyed by X-Call-Id for callback correlation
invoke_times = {}

def pick_tier(req, func_name):
    # 1) HEADER — *** tier decided here ***
    h=(req.headers.get("X-Tier") or "").strip().lower()
    if h in ("high","hi","h"): return f"{func_name}-hi-tier"
    if h in ("medium","med","m"): return f"{func_name}-med-tier"
    if h in ("low","lo","l"): return f"{func_name}-low-tier"
    # 2) Query, 3) JSON fallback
    q=(req.args.get("tier") or "").strip().lower()
    if q in ("high","hi","h"): return f"{func_name}-hi-tier"
    if q in ("medium","med","m"): return f"{func_name}-med-tier"
    if q in ("low","lo","l"): return f"{func_name}-low-tier"
    data=req.get_json(silent=True) or {}
    b=(data.get("tier") or "").strip().lower()
    if b in ("high","hi","h"): return f"{func_name}-hi-tier"
    if b in ("medium","med","m"): return f"{func_name}-med-tier"
    if b in ("low","lo","l"): return f"{func_name}-low-tier"
    return f"{func_name}-low-tier"

@app.post("/invoke/<func_name>")
def invoke(func_name):
    
    headers = { 'X-Callback-Url' : X_CALLBACK_ID }
    try:
        headers['Compute-Time'] = request.headers.get("Compute-Time")
    except:
        pass
    try:
        headers['X-Tier'] = request.headers.get("X-Tier")
    except:
        pass
    try:
        dataset = request.headers.get("X-Dataset")
        if not (dataset == 'amazon-reviews' or datatset == 'sms-spam'):
            print("Invalid 'X-Dataset' header. (Must be 'amazon-reviews' or 'sms-spam'.) Using 'sms-spam'...", flush=True)
            dataset = 'sms-spam'
        headers['X-Dataset'] = dataset
    except:
        if func_name == 'tfidf-vectorize':
            dataset = 'sms-spam'
            headers['X-Dataset'] = dataset
        else:
            dataset = None
    fn=pick_tier(request, func_name)
    
    json_data = request.get_json(silent=True)
    if isinstance(json_data, dict):
        payload = json_data.get("payload", {})
    elif isinstance(json_data, str):
        payload = json_data
    else:
        payload = {}
    
    print(f"Outgoing Request Headers (To OpenFaaS): {headers}", flush=True)
    invoke_time = time.time()
    r=requests.post(f"{GATEWAY}/async-function/{fn}", headers=headers, json=payload or {})
    print(f"Invocation Response Headers (from OpenFaaS): {r.headers}, {r.status_code}", flush=True)
    
    # Store invoke time for callback correlation
    call_id = r.headers.get('X-Call-Id')
    if call_id:
        invoke_times[call_id] = {
            'invoke_time': invoke_time,
            'tier': f"fn{'' if not dataset else f'-{dataset}'}",
            'gateway_arrival_time_ns': r.headers.get('X-Start-Time', '0')
        }
    
    if REQUEST_OUTPUT_FILE:
        try:
            invoke_time_human = datetime.fromtimestamp(invoke_time).strftime('%Y-%m-%d %H:%M:%S.%f')
            
            gateway_arrival_time_ns = r.headers.get('X-Start-Time', '0')
            x_start_time_sec = int(gateway_arrival_time_ns) / 1_000_000_000
            x_start_time_human = datetime.fromtimestamp(x_start_time_sec).strftime('%Y-%m-%d %H:%M:%S.%f')
            
            latency_ms = (x_start_time_sec - invoke_time) * 1000
            
            with open(REQUEST_OUTPUT_FILE, 'a', newline='') as rof:
                writer = csv.writer(rof)
                writer.writerow([
                    r.headers.get('X-Call-Id'), 
                    fn, 
                    f"{invoke_time:.6f}",  
                    invoke_time_human,
                    gateway_arrival_time_ns,
                    x_start_time_human,
                    f"{latency_ms:.3f}" 
                ])
        except Exception as e:
            print(f"Warning: Could not write to results CSV: {e}")
    
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","text/plain")})

@app.get("/healthz")
def healthz(): return "ok", 200

@app.post("/callback")
def callback():
    """
    Receive callback from OpenFaaS after function execution completes.
    This measures END-TO-END latency: from router invoke to function completion.
    """
    try:
        
        # print(f"request.headers: {request.headers}", , flush=True)
        
        callback_time = time.time()
        callback_time_human = datetime.fromtimestamp(callback_time).strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Get X-Call-Id from headers
        call_id = request.headers.get('X-Call-Id')
        
        if not call_id:
            print("⚠️  Callback received without X-Call-Id", flush=True)
            return jsonify({'status': 'error', 'message': 'Missing X-Call-Id'}), 400
        
        # Look up original invoke time
        if call_id not in invoke_times:
            print(f"⚠️  Callback received for unknown X-Call-Id: {call_id}", flush=True)
            return jsonify({'status': 'error', 'message': 'Unknown X-Call-Id'}), 404
        
        invoke_data = invoke_times[call_id]
        invoke_time = invoke_data['invoke_time']
        tier = invoke_data['tier']
        gateway_arrival_time_ns = invoke_data['gateway_arrival_time_ns']
        
        # Calculate end-to-end latency
        end_to_end_latency_ms = (callback_time - invoke_time) * 1000
        
        # Callback 'X-Start-Time' is actual function start time (Contrasted with initial request response 'X-Start-Time', which is gateway arrival time - This is assigned to invoke_data as 'gateway_arrival_time_ns' above in the invoke/{func} POST handler.)
        function_start_time_ns = request.headers.get('X-Start-Time')
        
        # Calculate queue wait time (gateway insertion to function start)
        queue_wait_ms = (int(function_start_time_ns) - int(gateway_arrival_time_ns)) / 1_000_000
        
        # Get function execution duration from OpenFaaS header and convert to ms
        x_duration_seconds = float(request.headers.get('X-Duration-Seconds', 0))
        execution_time_ms = x_duration_seconds * 1000
        
        # Router overhead (already calculated request response header)
        router_overhead_ms = ((int(function_start_time_ns) / 1_000_000_000) - invoke_time) * 1000
        
        print(f"Callback: {call_id[:8]}... | Tier: {tier} | E2E: {end_to_end_latency_ms:.2f}ms | Queue: {queue_wait_ms:.2f}ms | Exec: {execution_time_ms:.2f}ms | Status: {request.headers.get('X-Function-Status', '0')}", flush=True)

        # Write to callback CSV
        if CALLBACK_OUTPUT_FILE:
            try:
                with open(CALLBACK_OUTPUT_FILE, 'a', newline='') as cof:
                    writer = csv.writer(cof)
                    writer.writerow([
                        call_id,
                        tier,
                        f"{invoke_time:.6f}",
                        datetime.fromtimestamp(invoke_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                        f"{callback_time:.6f}",
                        callback_time_human,
                        f"{end_to_end_latency_ms:.3f}",
                        f"{router_overhead_ms:.3f}",
                        f"{queue_wait_ms:.3f}",
                        f"{execution_time_ms:.3f}",
                        gateway_arrival_time_ns,
                        function_start_time_ns,
                        request.headers.get('X-Duration-Seconds', '0'),
                        request.headers.get('X-Function-Status', '0'),
                        request.headers.get('X-Retry', '0'),
                        request.headers.get('X-Max-Retry', '0')
                    ])
            except Exception as e:
                print(f"⚠️  Error writing callback to CSV: {e}", flush=True)
        
        # Clean up invoke_times to prevent memory leak
        del invoke_times[call_id]
        
        return jsonify({'status': 'success', 'latency_ms': end_to_end_latency_ms}), 200
        
    except Exception as e:
        print(f"❌ Callback error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.post("/new-csv")
def new_csv():
    """Create new CSV files for a new experiment"""
    global REQUEST_OUTPUT_FILE, CALLBACK_OUTPUT_FILE
    
    # Get experiment name from request if provided
    data = request.get_json(silent=True) or {}
    exp_name = data.get('experiment_name', datetime.now().strftime("%Y%m%d%H%M%S"))
    
    # Create new CSV files
    REQUEST_OUTPUT_FILE = create_results_csv(
        filename=f"request-results_{exp_name}.csv", 
        kind="request"
    )
    CALLBACK_OUTPUT_FILE = create_results_csv(
        filename=f"callback-results_{exp_name}.csv",
        kind="callback"
    )
    
    # Clear invoke_times for new experiment
    invoke_times.clear()
    
    return jsonify({
        'status': 'success',
        'message': 'New CSV files created',
        'request_file': REQUEST_OUTPUT_FILE,
        'callback_file': CALLBACK_OUTPUT_FILE,
        'experiment': exp_name
    }), 200

@app.get("/current-csv")
def current_csv():
    """Get the current CSV file paths"""
    return jsonify({
        'request_file': REQUEST_OUTPUT_FILE,
        'callback_file': CALLBACK_OUTPUT_FILE,
        'pending_callbacks': len(invoke_times)
    }), 200

if __name__=="__main__":
    #app.run(host="0.0.0.0", port=5055, debug=True)
    app.run(host="0.0.0.0", port=5055)