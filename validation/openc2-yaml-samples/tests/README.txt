To convert from json to yaml:
for j in *.json; do yq -p json -o yaml $j >  ${j%json}yaml; done
