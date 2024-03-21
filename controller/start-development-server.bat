@ECHO OFF
kubectl create token testing -n digitaltwins
kubectl port-forward --namespace digitaltwins svc/minio 9000:9000