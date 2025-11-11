from kubernetes import client, config
import base64

def get_openfaas_basic_auth_pwd():

	# Load Kubernetes configuration
	config.load_kube_config()

	# Create a CoreV1Api client
	v1 = client.CoreV1Api()

	# Get the basic-auth secret from the openfaas namespace
	try:
		secret = v1.read_namespaced_secret(name="basic-auth", namespace="openfaas")
		
		# Extract and decode the password
		encoded_password = secret.data.get("basic-auth-password")
		if encoded_password:
			password = base64.b64decode(encoded_password).decode("utf-8")
			print(f"OpenFaaS Basic Auth Password: {password}")
			return password
		else:
			print("Basic auth password not found in the secret.")
			return "Basic auth password not found in the secret."

	except client.ApiException as e:
		print(f"Error accessing Kubernetes secret: {e}")
		return f"Error accessing Kubernetes secret: {e}"