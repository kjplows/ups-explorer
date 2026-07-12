import sys, subprocess, os
from pathlib import Path

deps_seen = set()
deps_to_do = {}

def process(args):
    sargs = [Path(Path.cwd() / "write_node.sh")]
    for av in args:
        sargs.append(av)
    subprocess.run(sargs)

    # Open up the dependency file
    depfile=f"node-{args[0]}-{args[1]}"
    if len(args) > 2:
        a2 = args[2].replace(':', '_')
        depfile=f"{depfile}-{a2}"
    depkey = f"{depfile[5:]}" # do it this way to prevent shallow copy
    depfile += ".tmp"

    seen_key = depkey.replace(':', '_')
    deps_seen.add(seen_key)

    with open(depfile, 'r') as fin:
        mydeps = []
        for line in fin:
            lset = line.strip().split(' ')
            depitem = f"{lset[0]}-{lset[1]}"
            if len(lset) > 2: # [2] is the '-q' flag
                l3 = lset[3].replace(':', '_')
                depitem = f"{depitem}-{l3}"

            mydeps.append(depitem)

        deps_to_do[depkey] = mydeps

        os.remove(depfile)

if __name__ == "__main__":

    # Process the root node
    process(sys.argv[1:])

    # And recurse until done
    while deps_to_do:
        pkey = next(reversed(list(deps_to_do.keys())))
        
        if not deps_to_do[pkey]:
            del deps_to_do[pkey]
            continue

        dep = deps_to_do[pkey].pop()
        deps = dep.split('-') 
        if( len(deps) > 2 ):
            deps[2] = deps[2].replace('_', ':')
            
        #print(dep, deps_seen)
        if dep in deps_seen:
            continue
        else:
            process(deps)
