#!/usr/bin/bash

usage () {
    echo "write_node.sh \$1 \$2 [$\3]"
    echo "\$1 : UPS package name"
    echo "\$2 : version"
    echo "\$3 : qualifier"
}

if [[ $# < 2 ]] || [[ $# > 3 ]] ; then
    usage
    exit 3
fi

product="$1 $2"
prettyname="$1-$2"
if [[ $# == 3 ]] ; then
    product=$product" -q $3"
    prettyname=$prettyname"-$(echo $3 | tr ':' '_')"
fi

shasum=$(sha256sum < <(echo "${product}") | awk -F " " '{print $1}')
shabridged=$(echo "${shasum}" | cut -c 1-16)

nodefile=cache/$1/${prettyname}-${shabridged}.json

<<EOF
if [[ -f ${nodefile} ]] ; then
    #echo "Product exists in cache, skipping"
    exit 0
fi
EOF

upcmd="ups depend ${product}"
#./parse_direct_dependencies.sh < <(ups depend sbndcode v10_06_00_09 -q e26:prof)
depcmd="./parse_direct_dependencies.sh < <(${upcmd})"
eval ${depcmd} > node-${prettyname}.tmp

echo -e "${OUTCYAN}Parsing $(cat node-${prettyname}.tmp | wc -l) direct dependencies of product ${OUTGREEN}${product}${OUTNOCOL}"

# start building a json node object in cache/

mkdir -p $(dirname ${nodefile})
cat <<EOF > ${nodefile}
{
  "product": "${product}",
  "name": "$1",
  "version": "$2",
EOF
if [[ $# == 3 ]] ; then
    echo -e "  \"qualifier\": \"$3\"," >> ${nodefile}
fi
cat <<EOF >> ${nodefile}
  "sha256": "${shasum}",
EOF

if [[ $(cat node-${prettyname}.tmp | wc -l) == 0 ]] ; then
    # No dependencies, finalise the leaf node
    echo -e "  \"leaf\": true" >> ${nodefile}
else
    echo -e "  \"dependencies\": [" >> ${nodefile}
    while IFS= read -r line ; do
	newsha=$(sha256sum < <(echo "${line}") | awk -F " " '{print $1}' | cut -c 1-16)
	echo -e "    {" >> ${nodefile}
	echo -e "      \"product\": \"${line}\"," >> ${nodefile}
	echo -e "      \"sha256\": \"${newsha}\"" >> ${nodefile}
	echo -e "    }" >> ${nodefile}
    done < <(cat node-${prettyname}.tmp)
    echo -e "  ]" >> ${nodefile}
fi
echo -e "}" >> ${nodefile}
