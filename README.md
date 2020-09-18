# knative-experiments


## Sockets on serving example
1.
```
$ kubectl apply -f rendezvous/service.yaml
```

2. Get the rendezvous service URL and put it in the socket service yaml as an env var with name RENDEZVOUS_ENDPOINT
```
$ kubectl get svc
```

3.
```
$ kubectl apply -f socket/service.yaml
```

4. Create a node pool, in this case its name is `test` and has a size of 3:
```
$ curl -X POST -G https://rendezvous.domain.example/pool/test -d "size=3"
```

5. Execute 3 worker pods (the requests will block until all 3 requests have been done):
```
curl -X GET -G https://sockets.domain.example/work -d "node=node1" -d "pool=test"
```
```
curl -X GET -G https://sockets.domain.example/work -d "node=node2" -d "pool=test"
```
```
curl -X GET -G https://sockets.domain.example/work -d "node=node3" -d "pool=test"
```



