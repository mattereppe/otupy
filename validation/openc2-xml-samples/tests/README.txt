To convert from json to yaml:
for j in *.json; do yq -p json -o xml $j > ${j%json}xml  ; done
Add tags expected by XMLEncoder:
for f in *xml; do gsed -e '1s/^/<OpenC2Msg>\n/' -e '$a\</OpenC2Msg>' -i $f ; done

Some messages required manual fixes:
- commands/good/query_features_empty_id.xml (empty target)
- query_features_empty.xml (empty target)
- status_asdouble.xml (converted to int)
- status_asstring.xml  (converted to int)
