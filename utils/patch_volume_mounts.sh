#!/bin/sh

# Patch the ml (tfidf-vectorize) deployments with volume mount
echo "Patching volume mount into tfidf-vectorize-hi-tier deployment..."
kubectl patch deployment tfidf-vectorize-hi-tier --type=strategic --patch-file patches/patch-for-pvc-on-tfidf-vectorize-hi-tier.yaml -n openfaas-fn
echo "Patching volume mount into tfidf-vectorize-med-tier deployment..."
kubectl patch deployment tfidf-vectorize-med-tier --type=strategic --patch-file patches/patch-for-pvc-on-tfidf-vectorize-med-tier.yaml -n openfaas-fn
echo "Patching volume mount into tfidf-vectorize-low-tier deployment..."
kubectl patch deployment tfidf-vectorize-low-tier --type=strategic --patch-file patches/patch-for-pvc-on-tfidf-vectorize-low-tier.yaml -n openfaas-fn

# Delete existing pods so new ones will be created with the patched deployment
echo "Deleting pre-existing tfidf-vectorize-hi-tier deployment pods..."
kubectl delete pods -l app=tfidf-vectorize-hi-tier -n openfaas-fn
echo "Deleting pre-existing tfidf-vectorize-med-tier deployment pods..."
kubectl delete pods -l app=tfidf-vectorize-med-tier -n openfaas-fn
echo "Deleting pre-existing tfidf-vectorize-low-tier deployment pods..."
kubectl delete pods -l app=tfidf-vectorize-low-tier -n openfaas-fn