# Tiered OpenFaaS: Hierarchical SLO Model

This project demonstrates a **multi-tiered Function-as-a-Service (FaaS)** setup built on **Kubernetes (k3d)** and **OpenFaaS**, featuring:
- **Three tiers** — `hi-tier`, `med-tier`, `low-tier`
- **Dynamic autoscaling** via Kubernetes HPA
- **Header-based routing** through a lightweight Flask pre-processor
- **Hierarchical SLO guarantees** (latency, cold-start probability, and availability differentiation)

---

## ⚙️ Architecture Overview
Client/Test Program (with X-Tier header)
↓
Flask Router (policy plane)
↓
OpenFaaS Gateway (control plane)
↓
Kubernetes (runtime plane)
├── Deployments (hi/med/low-tier)
├── HPAs (per-tier scaling)
└── Services (load-balanced access)
↓
Callback Handler

| Component | Role |
|------------|------|
| **Google Kubernetes Engine OR Docker Desktop + WSL2** | Container runtime for Kubernetes (Cloud OR Local Cluster) |
| **k3d (K3s in Docker)** | Lightweight local Kubernetes cluster (Or similar variant [e.g. KinD] - Needed for Local Cluster Only) |
| **OpenFaaS (Pro Standard License)** | Function-as-a-Service control plane |
| **faas-cli** | CLI for function lifecycle (build, publish, deploy) |
| **Flask Preprocessor and Callback Handler** | Routes requests based on `X-Tier` header and Logs Request and Callback Metrics |
| **Flask Test Program** | Various Options for Sending Invocation Requests to Preprocessor |

---

## 🧰 Prerequisites (GKE Cloud Cluster - Cloud Based Cluster)
<small>[Alternatively, skip to next section for local cluster install.]</small>
1. Use Cloud Shell in Google Cloud console (from Kubernetes Clusters page) or install Google Cloud CLI on local machine to access GKE cluster. (CLI install steps for Ubuntu below.)
* <small>Note, Google Cloud Shell can be used instead of the Google Cloud CLI, in which case step 1 can be skipped. However, to deploy the preprocessor as a container image using locally based .yaml files , Google Cloud CLI will be needed.</small>
<br>

```sh
# UBUNTU
sudo apt update
# If kubectl is not already installed
sudo snap kubectl --classic
# If helm is not already installed and will be used instead of Arkade for OpenFaaS installation (see step 5)
sudo snap helm --classic

# Install GCP CLI
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
gcloud components install gke-gcloud-auth-plugin

# Authenticate to GCP
gcloud auth login	# You'll probably need to paste a resulting URL into a browser to authenticate after running this command, depending on how your Google Cloud project and IAM-based access is configured.
gcloud config set project <your-project-name (e.g. festive-airway-476203-p2)>
gcloud auth list

# Fetch's cluster credentials and updates local kubeconfig file, setting newly added cluster as the current context
gcloud container clusters get-credentials <your-GKE-cluster-name (e.g.openfaas-cluster)> --region <your-region (e.g. us-central1-c)> --project <your-project-name  (e.g. festive-airway-476203-p2)>

# Kubernetes Credential
export USE_GKE_GCLOUD_AUTH_PLUGIN=True
```

2. Create a GKE (Google Kubernetes Engine) cluster manually.
* <small>Note, using GKE Autopilot cluster configuration may severely limit granular autoscaling configuration options, hence manual cluster creation is recommended, with steps provided below. Configuration can be modified as desired, these are only recommendations and reflect the experimental setup described in the paper that links to this repository.</small>
<br>

```sh
# GKE Set up (Manual - No Autopilot)
gcloud container clusters create openfaas-cluster \
--num-nodes=2 \
--machine-type=e2-standard-2 \
--zone=us-central1-c \
--enable-ip-alias \
--enable-dataplane-v2 \
--release-channel=regular

# Disable node autoscaling - minimize charges and keep experimentation to a fixed resource pool (Optional)
gcloud container clusters update openfaas-cluster \
	--no-enable-autoscaling \
	--node-pool default-pool \
	--zone us-central1-c

# Fetch's cluster credentials and updates local kubeconfig file, setting newly added cluster as the current context
gcloud container clusters get-credentials <your-GKE-cluster-name (e.g.openfaas-cluster)> --region <your-region (e.g. us-central1)> --project <your-project-name  (e.g. festive-airway-476203-p2)>

# Kubernetes Validation - Note if Autopilot was used for GKE cluster creation, nodes will likely not be deployed until OpenFaaS is installed (Step 5)
kubectl get ns
# Kubernetes Validation - Note if Autopilot was used for GKE cluster creation, pods will likely show status of pending until OpenFaaS is installed (Step 5)
	kubectl get pods -A
```


## 🧰 Prerequisites (Windows/WSL2 Setup - Single Node Local Cluster)
<small>[Skip this section if using a GKE cluster as described above.]</small>

1. Enable WSL2
```powershell
# Install/Setup Windows Linux Subsystem
wsl --install
# To enter Linux environment
wsl
```

Install Ubuntu from the Microsoft Store.
Install Docker Desktop
Enable: Use the WSL 2 based engine
Enable WSL integration for Ubuntu

After installing Ubuntu install dependencies
sudo apt-get update -y
sudo apt-get install -y curl git unzip python3 python3-pip python3-venv


2. Configure Docker Access in WSL

```sh
export DOCKER_HOST=unix:///mnt/wsl/shared-docker/docker.sock
sudo mkdir -p /var/run
sudo ln -sf /mnt/wsl/shared-docker/docker.sock /var/run/docker.sock
docker version
#Recommended to persist this
echo 'export DOCKER_HOST=unix:///mnt/wsl/shared-docker/docker.sock' >> ~/.bashrc
```


3. Install the required tools
```sh
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# helm
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```


4. Create the Kubernetes Cluster
```sh
k3d cluster create openfaas --agents 2 --wait
```

## 🪂 OpenFaaS Deployment ##

- _Without an OpenFaaS Pro Standard or Pro Enterprise license (i.e. when using the Community Edition), asynchronous function calls are only serviced one at a time (max_inflight=1). In other words, concurrency is unavailable. Therefore a Pro license is required to produce meaningful results for a tiered service demonstration. Non-Production/Education licenses may be available. Contact support via the "Setup a meeting" link at the bottom of this page: https://www.openfaas.com/pricing/_

1. (Option 1) Deploy OpenFaaS with Arkade (Preferred)
```sh
# Install arkade
curl -sLS https://get.arkade.dev | sudo sh

# faas-cli
curl -sSL https://cli.openfaas.com | sudo sh

## FOR GKE CLUSTERS
# Install OpenFaaS Pro -- 
arkade install openfaas --load-balancer \    #    service-tyype = LoadBalancer - to expose and external gateway IP address. (Use --loadBalancer with caution. Traffic is non-encrypted when managing/invoking functions via LoadBalancer. See: https://docs.openfaas.com/reference/tls-openfaas/ for additional security configuration methods.)
  --queue-mode function \    # queue-mode = function allows for queue-based scaling, scaling NATS consumers based on the number of functions active in the queue. See https://docs.openfaas.com/openfaas-pro/jetstream/ for additional details.
  --set queueWorkerPro.maxInflight=5    # Establish queue-based concurrency limit of 5, to ensure backpressure on NATS queue for queue based scaling, and to ensure function pods are not overwhelmed - There is also a function-level 'max-inflight' setting that defaults to 50 for each function
  --set queueWorkerPro.ackWait=5m    # Allow for slower running functions, such as ml inference (This doesn't seem to work from Arkade install, however, even though it doesn't throw an error when passing this argument as shown. Hence see optional step for manual kubernetes deployment patching at the end of this step.)
	or
# Install OpenFaaS Community -- Service Type = LoadBalancer - to expose and external gateway IP address. (Use --loadBalancer with caution. Traffic is non-encrypted when managing/invoking functions via LoadBalancer. See: https://docs.openfaas.com/reference/tls-openfaas/ for additional security configuration methods.)
arkade install openfaas --load-balancer \    #    service-tyype = LoadBalancer - to expose and external gateway IP address. (Use --loadBalancer with caution. Traffic is non-encrypted when managing/invoking functions via LoadBalancer. See: https://docs.openfaas.com/reference/tls-openfaas/ for additional security configuration methods.)
#  --queue-mode function \    # Not a valid flag for ce [arkade] install
#  --max-inflight 1    # NO OTHER OPTION HERE FOR COMMUNITY EDITION - CONCURRENCY IS NOT AVAILABLE

## FOR LOCAL CLUSTER
# Install OpenFaaS Pro -- Default Service Type = ClusterIP - For single node clusters with no externally facing gateway (e.g. local single node cluster) 
arkade install openfaas
    or
# Install OpenFaaS Community Edition -- Default Service Type = ClusterIP - For single node clusters with no externally facing gateway (e.g. local single node cluster) 
arkade install openfaas-ce

# Port-forward the gateway (Local cluster only - Port forwarding may vary if using non-default)
kubectl -n openfaas port-forward svc/gateway 8080:8080

# Optional - Extend Timeouts (Good for longer running functions, e.g. machine learning [e.g. tfidf-vectorize with amazon-reviews dataset (See container build ReadMe for more info.)]
kubectl patch deployment gateway --type=strategic -n openfaas --patch-file gateway-patch.yaml    # Found in utils/yaml
kubectl rollout restart deployment gateway -n openfaas
kubectl patch deployment queue-worker --type=strategic -n openfaas --patch-file queue-worker-patch.yaml    # Found in utils/yaml
kubectl rollout restart deployment queue-worker -n openfaas
```

2. (Option 2) Deploy OpenFaaS with Helm
```sh
# Namespaces (Optional)
kubectl create namespace openfaas --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace openfaas-fn --dry-run=client -o yaml | kubectl apply -f -

# Install OpenFaaS
helm repo add openfaas https://github.com/openfaas/faas-netes
helm repo update

## For GKE cluster, with externally facing gateway (Use serviceType=loadBalancer with caution. Traffic is non-encrypted when managing/invoking functions via LoadBalancer. See: https://docs.openfaas.com/reference/tls-openfaas/ for additional security configuration methods.)
helm upgrade -i openfaas openfaas/openfaas \
  --namespace openfaas \
  --set functionNamespace=openfaas-fn \
  --set generateBasicAuth=true \
  --set serviceType=LoadBalancer \
  --wait

## For single (e.g. local) node cluster without externally facing gateway
helm upgrade -i openfaas openfaas/openfaas \
  --namespace openfaas \
  --set functionNamespace=openfaas-fn \
  --set generateBasicAuth=true \
  --set serviceType=ClusterIP \
  --wait
  
# Port-forward the gateway (Local cluster only - Port forwarding may vary if using non-default)
kubectl -n openfaas port-forward svc/gateway 8080:8080
```

3. Authenticate to OpenFaaS
```sh
## FOR GKE CLUSTERS
# View the gateway service IPs and type - Must run kubectl commands in Cloud Shell via Google Cloud Console or using GCI to connect to GKE cluster [See step 2 under Prerequisites (Google GKE Cloud Cluster - Cloud Based Single- or Multi- Node Cluster]
kubectl get svc -n openfaas gateway-external    # If LoadBalancer service type was used at installation, should see gateway-external service with external IP
   or
kubectl get svc -n openfaas -o wide    # If LoadBalancer service type was used at installation, should see gateway-external service with external IP
export GATEWAY="<external-gateway-ipaddress:port-as-determined-above>"
export PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 -d)

## FOR LOCAL CLUSTER
# IN A NEW TERMINAL (If port forwarding established above - only applies to local cluster)
export GATEWAY="http://127.0.0.1:8080"
export PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 -d)

faas-cli login --username admin --password "$PASSWORD" --gateway $GATEWAY
faas-cli list --gateway $GATEWAY
```

4. Applying OpenFaaS Pro License (If Applicable)
```sh
# Delete existing license secret if one exists
kubectl delete secret -n openfaas openfaas-license		# If prior license secret exists

# Apply license from literal
kubectl create secret generic \
  -n openfaas \
  openfaas-license \
  --from-literal=license='<Your License Key Here>'

# Restart the deployment
kubectl rollout restart deployment -n openfaas
```
- _For additional information on applying OpenFaaS Pro License, see https://docs.openfaas.com/deployment/pro/_

5. Enable autoscaling per Tier (Community Edition Only - Not needed with Pro license. See https://docs.openfaas.com/architecture/autoscaling/ & https://www.openfaas.com/blog/custom-metrics-scaling/)
```sh
kubectl -n openfaas-fn autoscale deploy/hi-tier  --cpu=60% --min=3 --max=20
kubectl -n openfaas-fn autoscale deploy/med-tier --cpu=65% --min=1 --max=10
kubectl -n openfaas-fn autoscale deploy/low-tier --cpu=70% --min=1 --max=5
# checking the scaling
kubectl -n openfaas-fn get hpa
```

6. Build, Publish, and Deploy Function Images
```sh
docker login
export DH_USER="<your_dockerhub_username>"
# From root of repo...
cd funcs
faas-cli build -f stack.yaml --gateway $GATEWAY
faas-cli publish -f stack.yaml --gateway $GATEWAY
faas-cli deploy -f stack.yaml --gateway $GATEWAY

# Alternatively, the three commands above can be combined into one like this:
faas-cli up -f stack.yaml --gateway $GATEWAY

# List deployed functions
faas-cli list --gateway $GATEWAY

# For ml function (tfidf-vectorize), need to manually patch in volume mounts to deployments and restart pods. Use this script:
utils/patch_volume_mounts.sh
```

## 🏃 Running / Testing

1. Deploy and Run the Flask Preprocessor/Callback Handler as a Cluster Pod with LoadBalancer Service and Mount Persistent Storage For Logging (GKE Cluster Only)

* SEE THE [CONTAINER-BUILD README](https://github.com/UIUC-Cloud-Computing-Capstone/OpenFaaS-SLO-Tiering-Per-Invocation-Team6/blob/main/router/container-build/ReadMe.md). (Skip step 2.)

2. Run the Flask Preprocessor/Callback Handler (Local Cluster Only)

```sh
python3 -m venv .venv && source .venv/bin/activate (optional - creates python virtual environment)
pip install flask requests

export OF_USER=admin
export OF_PASS=$PASSWORD
export GATEWAY=http://127.0.0.1:8080	# Modify port if needed
# From repo root...
python -m router.app
```


2. Simple Load Testing & Scaling Validation
```sh
sudo apt-get install -y hey

#This loads for 60s 20 clients
faas-cli deploy -f stack.yaml --env hi-tier.BUSY_MS=100 --gateway $GATEWAY

hey -z 60s -c 20 -m POST \
  -H "Content-Type: application/json" \
  -H "X-Tier: high" \
  -d '{"payload":{"work":"simulate"}}' \
  http://<load-balancer-ingress-of-preprocessor-container-service(see CONTAINER-BUILD README)>/invoke/<function-name>
     or
  http://<locally-accessible-address>:5055/invoke/<function-name>	# Local Cluster Only - Need to determine locally accessible address using show network command (e.g. `ipconfig`). The app listens on all available addresses but you probably can't use 127.0.0.1 because it is in use by the OpenFaaS cluster.


# Watching autoscaling (will only work with OpenFaaS Pro license)
watch -n 1 'kubectl -n openfaas-fn get hpa,deploy | grep -E "NAME|tier"'

    or

# Get autoscaler logs (watch interactively, last 30 seconds)
kubectl logs -n openfaas deploy/autoscaler --since 30s -f

#Inspect details
kubectl -n openfaas-fn describe hpa hi-tier
kubectl -n openfaas-fn get pods -l faas_function=hi-tier -w
kubectl -n openfaas-fn top pods | grep hi-tier

```

3. Full Testing & Scaling Validation

* SEE [README.txt](https://github.com/UIUC-Cloud-Computing-Capstone/OpenFaaS-SLO-Tiering-Per-Invocation-Team6/blob/main/Testing/README.txt) FOR DETAILS ON RUNNING THE TEST PROGRAM [funTest.py](https://github.com/UIUC-Cloud-Computing-Capstone/OpenFaaS-SLO-Tiering-Per-Invocation-Team6/blob/main/Testing/funTest.py)
