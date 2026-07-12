#!/usr/bin/env python3

from pathlib import Path
from collections import defaultdict
import argparse
import json
import html
import pickle # so I don't have to regenerate the cache every load

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
)

##############################################################################

class Cache:

    def __init__(self, root="cache"):

        self.root = Path(root)

        self.sha_index = {}
        self.package_index = defaultdict(list)

        self.build()


    ##########################################################################

    def build(self):

        print("Building cache index...")

        for filename in self.root.rglob("*.json"):

            sha = filename.stem[-16:]

            with open(filename) as f:
                node = json.load(f)

            if node["sha256"][:16] != sha:
                raise RuntimeError(
                    f"SHA mismatch: {filename}"
                )

            self.sha_index[sha] = filename
            self.package_index[node["name"]].append(node)


        print(
            f"Loaded {len(self.sha_index)} builds "
            f"for {len(self.package_index)} packages"
        )


    ##########################################################################

    def nodes(self, package):

        return self.package_index.get(package, [])


    ##########################################################################

    def load(self, node):

        with open(self.sha_index[node["sha256"]]) as f:
            return json.load(f)


    ##########################################################################

    def versions(self, package):

        """
        Unique versions.
        """

        seen = set()
        result = []

        for node in self.package_index.get(package, []):

            item =node["version"]

            if item not in seen:
                result.append(item)
                seen.add(item)

        return sorted(result)

    def qualifiers(self, package):

        """
        Unique qualifiers.
        """

        seen = set()
        result = []

        for node in self.package_index.get(package, []):

            item = node.get("qualifier", "")

            if item not in seen:
                result.append(item)
                seen.add(item)
                
        result.append("NOQUAL")

        return sorted(result)


    ##########################################################################

    def find(self, package, version, qualifier):

        for node in self.nodes(package):

            if node["version"] != version:
                continue

            if node.get("qualifier", "") != qualifier:
                continue

            return node

        return None


    ##########################################################################

    def abstract_dependencies(self, package):

        deps = set()

        for node in self.nodes(package):

            for dep in node.get("dependencies", []):

                deps.add(
                    dep["product"].split()[0]
                )

        return sorted(deps)


    ##########################################################################

    def abstract_parents(self, package):

        parents = set()

        for parent in self.package_index:

            for node in self.nodes(parent):

                for dep in node.get("dependencies", []):

                    if dep["product"].split()[0] == package:
                        parents.add(parent)

        return sorted(parents)

    ##############################################################################

    # Code to generate SVGs for visualisation of abstract dep trees

    def abstract_graph_svg(self, package, concrete=None):

        parents = self.abstract_parents(package)

        if concrete:
            deps = [
                self.parse_product(d["product"])
                for d in concrete.get("dependencies", [])
            ]
            centre = {
                "name": concrete["name"],
                "version": concrete["version"],
                "qualifier": concrete.get("qualifier", "")
            }
        else:
            deps = [
                {
                    "name": d,
                    "version": "",
                    "qualifier": ""
                }
                for d in self.abstract_dependencies(package)
            ]
            centre = {
                "name": package,
                "version": "",
                "qualifier": ""
            }

        ##################################################################
        # Geometry
        ##################################################################

        rows = max(len(parents), len(deps), 1)

        box_h = 80 if concrete else 40
        box_w = 320

        row_height = box_h + 30

        margin = 50
        
        graph_height = rows * row_height + 2 * margin

        graph_width = 1200

        left_x = 80
        centre_x = graph_width // 2
        right_x = graph_width - box_w - 80

        centre_y = graph_height / 2

        def ypos(i, count):
            
            if count == 0:
                return centre_y

            return (margin + (i + 0.5) * (graph_height-2*margin) / count)

        def text_box(x, y, data):
            lines = [data["name"]]
            if data["version"]:
                lines.append(data["version"])
            if data["qualifier"]:
                lines.append(data["qualifier"])
                
            out = []

            start = y - ((len(lines)-1) *18/2)
            
            for i, line in enumerate(lines):

                out.append(
                    f'<text '
                    f'x="{x}" '
                    f'y="{start + i*18}" '
                    f'font-size="16" '
                    f'text-anchor="middle" '
                    f'dominant-baseline="middle">'
                    f'{html.escape(line)}'
                    f'</text>'
                )

            return "\n".join(out)

        svg = []

        svg.append(
            f'<svg '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {graph_width} {graph_height}" '
            f'width="100%">'
        )

        ##################################################################
        # Parents
        ##################################################################

        for i, parent in enumerate(parents):
            y = ypos(i,len(parents))
        
            svg.append(
                f'<line '
                f'x1="{left_x+box_w}" '
                f'y1="{y}" '
                f'x2="{centre_x-box_w/2}" '
                f'y2="{centre_y}" '
                f'stroke="black"/>'
            )


            svg.append(
                f'<a href="/package/{parent}/">'
            )


            svg.append(
                f'<rect '
                f'x="{left_x}" '
                f'y="{y-box_h/2}" '
                f'width="{box_w}" '
                f'height="{box_h}" '
                f'rx="6" ry="6" '
                f'fill="#FFF8DC" '
                f'stroke="black"/>'
            )


            svg.append(
                text_box(
                    left_x + box_w/2,
                    y,
                    {
                        "name": parent,
                        "version": "",
                        "qualifier": ""
                    }
                )
            )


            svg.append("</a>")

            ##################################################################
            # Centre package
            ##################################################################
            
        svg.append(
            f'<rect '
            f'x="{centre_x-box_w/2}" '
            f'y="{centre_y-box_h/2}" '
            f'width="{box_w}" '
            f'height="{box_h}" '
            f'rx="6" ry="6" '
            f'fill="#DDEEFF" '
            f'stroke="black"/>'
        )


        svg.append(
            text_box(
                centre_x,
                centre_y,
                centre
            )
        )



        ##################################################################
        # Dependencies
        ##################################################################

        for i, dep in enumerate(deps):
            
            y = ypos(i,len(deps))

            svg.append(
                f'<line '
                f'x1="{centre_x+box_w/2}" '
                f'y1="{centre_y}" '
                f'x2="{right_x}" '
                f'y2="{y}" '
                f'stroke="black"/>'
            )

            svg.append(
                f'<a href="/package/{dep["name"]}/">'
            )

            svg.append(
                f'<rect '
                f'x="{right_x}" '
                f'y="{y-box_h/2}" '
                f'width="{box_w}" '
                f'height="{box_h}" '
                f'rx="6" ry="6" '
                f'fill="#E6FFE6" '
                f'stroke="black"/>'
            )

            svg.append(
                text_box(
                    right_x + box_w/2,
                    y,
                    dep
                )
            )

            svg.append("</a>")

        svg.append("</svg>")

        return "\n".join(svg)

    ##############################################################################

    # Product parser for when concrete builds are to be drawn

    def parse_product(self, product):

        fields = product.split()

        result = {
            "name": fields[0],
            "version": "",
            "qualifier": "",
        }

        if len(fields) > 1:
            result["version"] = fields[1]

        if "-q" in fields:

            q = fields.index("-q")

            if q + 1 < len(fields):
                result["qualifier"] = fields[q + 1]

        return result


##############################################################################

app = Flask(__name__)

cache = None


##############################################################################

@app.route("/")
def index():

    return render_template(
        "index.html",
        packages = cache.package_index
    )


##############################################################################

@app.route("/search")
def search():

    name = request.args.get("package", "").strip()

    if name not in cache.package_index:

        return render_template(
            "index.html",
            packages = cache.package_index,
            warning=f"Package '{name}' not found"
        )


    return redirect(
        url_for(
            "package",
            name=name
        )
    )


##############################################################################

@app.route("/package/<name>/")
def package(name):

    if name not in cache.package_index:
        abort(404)


    version = request.args.get("version")
    qualifier = request.args.get("qualifier")
    if(qualifier == "NO QUALIFIER" or qualifier == "NOQUAL"):
        qualifier = ""

    concrete = None
    warning = None


    if version or qualifier:

        concrete = cache.find(
            name,
            version,
            qualifier or ""
        )


        if concrete is None:

            warning = (
                f"No build found for "
                f"{name} {version} "
                f"{qualifier}"
            )


    # Reverse the version list so that newer versions come up first
    versions = cache.versions(name)
    versions.reverse()
    
    return render_template(
        "package.html",

        package=name,

        versions=versions,
        qualifiers=cache.qualifiers(name),

        abstract_dependencies=
            cache.abstract_dependencies(name),

        abstract_parents=
            cache.abstract_parents(name),

        abstract_graph=
            cache.abstract_graph_svg(name, concrete),

        concrete=concrete,

        warning=warning,

    )


##############################################################################

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cache",
        default="cache",
        help="Cache directory to use"
    )

    parser.add_argument(
        "--rebuild",
        action='store_true',
        help="Rebuild cache index (slows down startup)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Open localhost on this port."
    )

    args = parser.parse_args()


    INDEX_FILE = Path(f"{args.cache}/cache_index.pkl")
    if INDEX_FILE.exists() and not args.rebuild:
        with INDEX_FILE.open('rb') as fpin:
            cache = pickle.load(fpin)
    else:
        cache = Cache(args.cache)
        with INDEX_FILE.open('wb') as fpout:
            pickle.dump(cache, fpout)

    app.run(
        host="127.0.0.1",
        port=args.port,
        debug=True,
        use_reloader=False,
    )
