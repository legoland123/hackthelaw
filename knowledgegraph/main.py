import pandas as pd
import networkx as nx

# === Load data ===
acts = pd.read_csv("acts.csv", encoding="cp1252")
provisions = pd.read_csv("provisions.csv", encoding="cp1252")
cases = pd.read_csv("data.csv", encoding="cp1252")
links = pd.read_csv("links.csv", encoding="cp1252")

print("Acts columns:", acts.columns.tolist())
print("Provisions columns:", provisions.columns.tolist())
print("Cases columns:", cases.columns.tolist())
print("Links columns:", links.columns.tolist())

acts.rename(columns={"ï»¿id": "id"}, inplace=True)
provisions.rename(columns={"ï»¿id": "id"}, inplace=True)
links.rename(columns={"ï»¿id": "id"}, inplace=True)

# === Create graph ===
G = nx.DiGraph()

# --- Add Act nodes ---
for row in acts.itertuples(index=False):
    G.add_node(
        row.id,
        label="Act",
        name=row.name if "name" in acts.columns else getattr(row, "title", None)
    )

# --- Add Provision nodes (linked to Acts) ---
for row in provisions.itertuples(index=False):
    G.add_node(
        row.id,
        label="Provision",
        provision=row.provision,
        type=row.type
    )
    # Link provision → its Act
    if pd.notna(row.actId):
        G.add_edge(row.id, row.actId, relation="partOf")

# --- Add Case nodes ---
for row in cases.itertuples(index=False):
    G.add_node(
        row.id,
        label="Case",
        name=row.caseName,
        summary=row.caseSummary,
        outcome=row.caseOutcome
    )

# --- Add Links: Case → Provision ---
for row in links.itertuples(index=False):
    if pd.notna(row.id) and pd.notna(row.provisionId):
        G.add_edge(row.id, row.provisionId, relation="cites")

# === Save graph ===
print("Graph has", G.number_of_nodes(), "nodes and", G.number_of_edges(), "edges")
nx.write_graphml(G, "legal_kg.graphml")
print("Graph saved to legal_kg.graphml")

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())

# Find provisions cited most often
provision_citations = [
    (n, G.in_degree(n)) for n, d in G.nodes(data=True) if d.get("label") == "Provision"
]
print(sorted(provision_citations, key=lambda x: x[1], reverse=True)[:10])