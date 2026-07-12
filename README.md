# ups-explorer
A small visualisation tool for UPS product stacks. Disclaimer: A bunch of the frontend Flask code has been vibe-coded with ChatGPT, though I try to validate output as much as possible. Caveat emptor.

## Setup

You'll need python > 3.9 (I use 3.14.3). Install + upgrade `pip`, and install the attached `requirements.txt`.

Untar the `cache.tar.gz` file in the same directory where `app.py` lives.

## Usage

### Building a UPS cache

You may use the provided `cache/cache_index.pkl` file I have included. In this case, skip this section.

If you want to add to the cache, see this section.

This step needs the system python on SBND gpvms avaialble with the SL7 container (python 3.6.8).

You should be on the SL7 container.

Source the setup script, `setup_products.sh` - this will get you SBND, ICARUS, SBN, LArSoft, and FNAL stacks.

To build a cache, make sure you can "see" a product using `ups list -aK+ <product_name>`, then run
```
while IFS= read -r line ; do python3 build_cache.py ${line} ; done < <(ups list -aK+ <product_name> | awk -F " " '{print $1" "$2" "$4}' | tr -d "\"" | sort -r -k2,2)
```

Wait until the cache has finished working. You can add more steps to the cache later.

### Running the app

This uses Flask to run. It exposes a port on your `localhost` which you can open with any browser as `http://localhost:<port_no>`. Note the protocol is http, not https.

```
python3 app.py -h

usage: app.py [-h] [--cache CACHE] [--rebuild] [--port PORT]

options:
  -h, --help     show this help message and exit
  --cache CACHE  Cache directory to use (default: cache/)
  --rebuild      Rebuild cache index (slows down startup)
--port PORT      Open localhost on this port (default: 8080)
```

For example, `python3 app.py` opens port 8080 so use `localhost:8080`. Navigating to `http://localhost:8080` in any browser will give you

<img width="1919" height="1005" alt="image" src="https://github.com/user-attachments/assets/1d683b66-51b8-4b9b-ae68-5fa7fa2999a2" />

You can type any package name in the box, or click one of the common packages. 

This can show you _abstract_ dependency graphs (no versions / qualifiers attached) by default:

<img width="1914" height="1003" alt="image" src="https://github.com/user-attachments/assets/a237a14e-7314-476e-ba5a-443377199baa" />

or you can type in / select a version + qualifier combo to get a _concrete_ graph, using the `Version` and `Qualifier` dialogue boxes on the top right and clicking `Load`:

<img width="1917" height="1005" alt="image" src="https://github.com/user-attachments/assets/a6453b16-fdbe-4293-89ce-fdb8389d6d31" />

In this abstract graph, package `nusystematics` is a direct dependency of `sbncode`, and has two direct dependencies (`nugen` and `systematicstools`). 
The concrete graph for `nusystematics v1_05_10sbn02 -q e26:prof` tells you that it depends on `nugen v1_23_01sbn02 -q e26:prof` and `systematicstools v01_04_04 -q e26:prof`. 

### Coloured bash output

If you want coloured terminal output, add the following to your `~/.bash_profile` (thanks to R. Hatcher!)
```
if [ -z "$PS1" ] || [ : ] ; then
  # if $- contains "i" then interactive session
  export ESCCHAR="\x1B" # or \033 # Mac OS X bash doesn't support \e as esc?
  export OUTBLACK="${ESCCHAR}[0;30m"
  export OUTBLUE="${ESCCHAR}[0;34m"
  export OUTGREEN="${ESCCHAR}[0;32m"
  export OUTCYAN="${ESCCHAR}[0;36m"
  export OUTRED="${ESCCHAR}[0;31m"
  export OUTPURPLE="${ESCCHAR}[0;35m"
  export OUTORANGE="${ESCCHAR}[0;33m" # orange, more brownish?
  export OUTLTGRAY="${ESCCHAR}[0;37m"
  export OUTDKGRAY="${ESCCHAR}[1;30m"
  # labelled "light but appear in some cases to show as "bold"
  export OUTLTBLUE="${ESCCHAR}[1;34m"
  export OUTLTGREEN="${ESCCHAR}[1;32m"
  export OUTLTCYAN="${ESCCHAR}[1;36m"
  export OUTLTRED="${ESCCHAR}[1;31m"
  export OUTLTPURPLE="${ESCCHAR}[1;35m"
  export OUTYELLOW="${ESCCHAR}[1;33m"
  export OUTWHITE="${ESCCHAR}[1;37m"
  export OUTNOCOL="${ESCCHAR}[0m" # No Color
fi
# use as:   echo -e "${OUTRED} this is red ${OUTNOCOL}"
```

### Feedback

For suggestions or requests please ping me on SBN slack (@John Plows) or send me an email.
