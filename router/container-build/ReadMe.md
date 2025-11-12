## Preprocessor Deployment Steps

### Build and push init container image to DockerHub

From container-build/init-container directory

1) Build Image
  - `docker build -t <your-dockerhub-repo>/openfaas-tiering-nfs-pvc-init:latest .`
  
2) Push Image to Dockerhub
  - `docker push <your-dockerhub-repo>/openfaas-tiering-nfs-pvc-init:latest`

### Build and push app.py (preprocessor) container image to DockerHub

From container-build directory (i.e. directory where this ReadMe.md is stored)...

1) Build Image
  - `docker build -t <your-dockerhub-repo>/openfaas-preprocessor:latest .`
  
2) Push Image to Dockerhub
  - `docker push <your-dockerhub-repo>/openfaas-preprocessor:latest`
  
### Kubernetes Deployment

From container-build/yaml directory (e.g. `cd yaml`, if coming from previous step), and with Kube context set to GKE OpenFaaS cluster[^1] ...

1) Create the kubernetes namespace on the existing cluster
  - `kubectl create namespace openfaas-tiering`

2a) Create GCE Persistent Disk in same zone as cluster.
 - `gcloud compute disks create gce-nfs-disk --size=10Gi --type=pd-standard --zone=us-central1-c`    # Minimum is 10Gi

2b) Define and Deploy the NFS Server - Mounts physical GKE Disk
- `kubectl apply -f nfs-server.yaml`

2c) Exec into the file share server and create /exports/app directory 

* <small>Can't get cmd to work from deployment file above [nfs-server.yaml]. It will make the directory but then seems to crash the container. See line 48-50 in nfs-server.yaml. But because we are using gce persistent disk with 'persistentVolumeReclaimPolicy: Retain' in our persistent volume configuration, this directory only has to be created once, even if the nfs-server pod has to be recreated from image. The mounted nfs storage will not lose it's files.)</small>

- `kubectl get pods -l role=nfs-server -n openfaas-tiering    # Get name of nfs-server pod`

- `kubectl exec -it <name-of-nfs-server-pod> -n openfaas-tiering -- /bin/bash    # Exec into it`

- `mkdir -p exports/app    # Make the shared directory`

- `exit`

2d) Define and Deploy the NFS PV and PVC - Links server service to logical pvc, so cluster apps can access mounted physical storage
- `kubectl apply -f nfs-pv-pvc.yaml`

- `kubectl get pvc nfs-pvc -n openfaas-tiering    # Make sure pvc is bound`
  
3) Apply config map to cluster (used for initContainer in deployment, primarily to set up ml function related files)
  - `kubectl apply -f init-container-script-configmap.yaml`
  
4) Run job to load nfs-pvc with ml-related files from container
 - `kubectl apply -f initialize-openfaas-tiering-nfs-pvc-job.yaml`
  
5) Apply app deployment - MODIFY IMAGE LOCATIONS AS NEEDED (lines 21 and 45 of openfaas-preprocessor-deployment.yaml)
  - `kubectl apply -f openfaas-preprocessor-deployment.yaml`
  
6) For tfidf-vectorize deployments only, manually patch the deployment to add the pvc mount (May need to rerun these commands after any redeployment of the functions.) -- See ../utils/patch_volume_mounts.sh
- `kubectl patch deployment tfidf-vectorize-<hi|med|low>-tier --type=strategic --patch-file patch-for-pvc-on-tfidf-vectorize.yaml -n openfaas-fn`

- `kubectl delete pods -l app=tfidf-vectorize-<hi|med|low>-tier -n openfaas-fn`

- `kubectl get deployment tfidf-vectorize-<hi|med|low>-tier -n openfaas-fn -o yaml    # To verify the patch`

7) Apply LoadBalancer service (for externally facing endpoint)
  - `kubectl apply -f openfaas-preprocessor-service.yaml`
  
### Extracting Results files

 - `kubectl -n openfaas-preprocessor cp <nfs-server-pod-name(created in step 2b)>:/exports/app/data/results <local-target-directory>`
 
### Trigger the creation of a new set of result files
<small>[This can also be accomplished by restarting the pod via kubectl rollout restart... (see below).]</small>

* Either sent a POST request to the preprocessor with '/new-csv' in the path (e.g.http://<preprocessor-external-gateway-external-ip>/new-csv>
  or
* Restart the preprocessor
- `kubectl rollout restart deployment/openfaas-preprocessor -n openfaas-tiering`
  
### Verify / Troubleshooting

- `kubectl get pods -n openfaas-preprocessor`

##### If logs are needed for troubleshooting

- `kubectl describe pod <pod-name> -n openfaas-preprocessor    # If pod is stuck creating a container or otherwise can't get to 'running' state

- `kubectl logs <pod-name> -n openfaas-tiering`

- `kubectl logs -n openfaas -l app=queue-worker --tail=200`

##### If needing to delete the deployment after deploying (to then redeploy)...
- `kubectl delete deployment openfaas-preprocessor -n openfaas-tiering`

##### If needing to delete pods after redeploying...
- `kubectl delete --all pods --namespace=openfaas-tiering`

##### To restart deployment
- `kubectl rollout restart deployment/openfaas-preprocessor -n openfaas-tiering`

##### Exec into pod's shell
- `kubectl -n openfaas-tiering exec -it <pod-name> -- /bin/bash`
    or
- `kubectl -n openfaas-tiering exec -it deployment/openfaas-preprocessor -c openfaas-preprocessor -- /bin/bash`

#### Create a temporary pod for debugging from image
- `kubectl run debug-pod --image=<your-image-name> -it --rm -- /bin/sh`

#### Check logs of initialization container
- `kubectl logs pod <pod-name> -c init-container -n openfaas-tiering`
    or
- `kubectl logs deployment/openfaas-preprocessor -c init-container -n openfaas-tiering`

#### Get pods that ran initialize-openfaas-fn-pvc job, then get logs
- `kubectl get pods -l job-name=initialize-openfaas-fn-pvc -n openfaas-fn`

- `kubectl logs <job-pod-name-determined-with-previous-command> -n openfaas-fn

#### Use this for a pvc inspector pod (for  openfaas-tiering-ml-data-pvc-inspector) if needed (to verify file copy to pvc)
- `kubectl apply -f openfaas-fn-data-pvc-inspector.yaml`

- `kubectl exec -it openfaas-fn-data-pvc-inspector -n openfaas-fn -- sh`

#### Use this for a pvc inspector pod (for openfaas-preprocessor-pvc-inspector) if needed (to verify file copy to pvcs)
- `kubectl apply -f openfaas-preprocessor-pvc-inspector.yaml`

- `kubectl exec -it openfaas-preprocessor-pvc-inspector -n openfaas-tiering -- sh`

#### Force deleting a pvc if stuck in terminating state (Use with caution)
- `kubectl patch pvc <pvc-name> -p '{"metadata":{"finalizers":null}}' --type=merge -n openfaas-tiering`

### Make sure the LoadBalancer service is associated to preprocessor pod, and determine IP address

##### Describe service ('LoadBalancer Ingress' is external IP)

- `kubectl describe svc -n openfaas-tiering`

##### Get service (External IP should match LoadBalancer Ingress from previous command - Note Selector for next command.)

- `kubectl describe svc -n openfaas-tiering`

##### Make sure preprocessor pod is labeled the same as the service's selector (as determined using previous command).

- `kubectl get pods -l app=openfaas-preprocessor -n openfaas-tiering`

<br>

[^1]: See the main 'ReadMe.md' file at the project root directory for more details about setting up GCI for interacting with a GKE cluster.