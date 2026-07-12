#!/usr/bin/bash

<<EOF
awk '
{
   for (i = 1; i <= NF; i++) {
      if ($i == "-f" || $i == "-z") {
         i++      # Skip this and following field
         continue
      }
      printf "%s%s", $i, (i == NF ? ORS : OFS) # O(R/F)S == Output (Record / Field) Separator
   }
}
'< <(./extract_direct_dependencies.sh $1)
EOF

awk '
{
   out = ""
   for (i = 1; i <= NF; i++) {
      if ($i == "-f" || $i == "-z") {
        i++
        continue
      }
      out = out (out ? OFS : "") $i
   }
   print out
}
'< <(./extract_direct_dependencies.sh $1)
