#!/usr/bin/env python3
"""
Convert INDRA REACH output to BEL (JSON) for comparison with LLM results.
Requires:  indra[bel]  pybel
"""

import json
import sys
from pathlib import Path

from indra.statements import stmts_from_json
from indra.assemblers.pybel import PybelAssembler
import pybel                              # BEL core library

# ---------------------------------------------------------------------
# 1. paths
# ---------------------------------------------------------------------
if len(sys.argv) != 2:
    sys.exit("Usage: python indra_to_bel.py <indra_reach_results.json>")

indra_path = Path(sys.argv[1])
graph_out = indra_path.with_name("indra_bel.nodelink.json")
flat_out = indra_path.with_name("indra_bel_statements.json")

# ---------------------------------------------------------------------
# 2. load INDRA statements
# ---------------------------------------------------------------------
raw = json.loads(indra_path.read_text())

stmts_json = []
for para in raw["INDRA_REACH_extractions"]:
    stmts_json.extend(para["Results"])

stmts = stmts_from_json(stmts_json)
print(f"Loaded {len(stmts)} INDRA statements")

# ---------------------------------------------------------------------
# 3. build BELGraph
# ---------------------------------------------------------------------
pba = PybelAssembler(stmts)          # positional arg works in all INDRA 1.x
bel_graph = pba.make_model()

# ---------------------------------------------------------------------
# 4. loss-less Node-Link JSON  (extension tells pybel.dump what to write)
# ---------------------------------------------------------------------
nodelink_dict = pybel.to_nodelink(bel_graph)           # documented helper
graph_out.write_text(json.dumps(nodelink_dict, indent=2))
print("wrote", graph_out)

flat = {"INDRA_BEL_extractions": []}
for para in raw["INDRA_REACH_extractions"]:
    idx = para.get("Index", "")               # e.g. "3"
    evidence = para.get("Evidence", "")            
    stmt_json_list = para["Results"]            # list of INDRA stmt dicts

    # build a BELGraph just for this evidence
    para_stmts = stmts_from_json(stmt_json_list)
    para_graph = PybelAssembler(para_stmts).make_model()

    # collect BEL → evidence mapping
    bel_to_evs = {}
    for u, v, data in para_graph.edges(data=True):
        bel_line = para_graph.edge_to_bel(u, v, data)

        ev_field = data.get("evidence")
        if ev_field is None:
            ev_texts = []
        elif isinstance(ev_field, str):                       # JSON-string
            ev_texts = [ev_field]
        elif isinstance(ev_field, list):                      # list[Evidence]
            ev_texts = [getattr(e, "text", str(e)) for e in ev_field]
        else:                                                 # single Evidence
            ev_texts = [getattr(ev_field, "text", str(ev_field))]

        bel_to_evs.setdefault(bel_line, []).extend(ev_texts)   

    # now append block to flat
    flat["INDRA_BEL_extractions"].append({
        "Index": idx,
        "Evidence": evidence,
        "Results": [
            {"bel_statement": bl, "evidence": sorted(set(evs))}
            for bl, evs in bel_to_evs.items()
        ]
    })

# pretty-print to disk
flat_out.write_text(json.dumps(flat, indent=2))
print("Wrote", len(flat["INDRA_BEL_extractions"]),
      "paragraph blocks →", flat_out)
