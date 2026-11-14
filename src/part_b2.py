import networkx as nx

# Sample data .
# Entities in the Maria Gomez article follow the B1 *reference* labels.
NODES = {
    "article:a1": "Article",  # "Maria Gomez, CEO of Northwind Logistics, announced a partnership with the city of Denver."
    "article:a2": "Article",  # "Tech Firm Announces Layoffs"
    "article:a3": "Article",  # "Tech Firm Opens New Office"
    "person:Maria Gomez": "Person",
    "person:Raj Mehta": "Person",
    "person:Ana Silva": "Person",  # mentioned in no article
    "org:Northwind Logistics": "Organization",
    "org:Contoso Tech": "Organization",
    "org:Fabrikam Capital": "Organization",
    "loc:Denver": "Location",
    "loc:Austin": "Location",
}

TRIPLES = [
    ("person:Maria Gomez", "worksAt", "org:Northwind Logistics"),
    ("person:Raj Mehta", "worksAt", "org:Contoso Tech"),
    ("org:Northwind Logistics", "locatedIn", "loc:Denver"),
    ("org:Contoso Tech", "locatedIn", "loc:Austin"),
    ("article:a1", "mentions", "person:Maria Gomez"),
    ("article:a1", "mentions", "org:Northwind Logistics"),
    ("article:a1", "mentions", "loc:Denver"),
    ("article:a2", "mentions", "person:Raj Mehta"),
    ("article:a2", "mentions", "org:Contoso Tech"),
    ("article:a3", "mentions", "person:Raj Mehta"),
    ("article:a3", "mentions", "org:Contoso Tech"),
    ("article:a3", "mentions", "org:Fabrikam Capital"),
]


def build_graph(
    nodes: dict[str, str], triples: list[tuple[str, str, str]]
) -> nx.DiGraph:
    """Build the directed entity graph from the node types and triples."""
    G = nx.DiGraph()

    for node_id, node_type in nodes.items():
        G.add_node(node_id, type=node_type)

    # Nodes are never created here: an endpoint missing from NODES would otherwise be added silently, with no type attribute.
    for src, relation, dst in triples:
        if src not in G or dst not in G:
            raise ValueError(f"Triple references unknown node: {(src, relation, dst)}")
        G.add_edge(src, dst, relation=relation)

    return G


def find_co_mentioned_organizations(G: nx.DiGraph, person_id: str) -> list[str]:
    """Return organizations mentioned in any article that mentions ``person_id``.

    Results are sorted node IDs without duplicates. Unknown IDs and non-Person
    nodes return an empty list.
    """
    if person_id not in G or G.nodes[person_id].get("type") != "Person":
        return []

    orgs: set[str] = set()
    # Two hops: person <- article (mentions), then article -> organization (mentions).
    for article_id, _, in_data in G.in_edges(person_id, data=True):
        if (
            in_data.get("relation") == "mentions"
            and G.nodes[article_id].get("type") == "Article"
        ):
            for _, target_id, out_data in G.out_edges(article_id, data=True):
                if (
                    out_data.get("relation") == "mentions"
                    and G.nodes[target_id].get("type") == "Organization"
                ):
                    orgs.add(target_id)

    return sorted(orgs)


def main() -> None:
    """Build the graph and report co-mentioned organizations per person."""
    G = build_graph(NODES, TRIPLES)
    print(f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    for node_id, data in sorted(G.nodes(data=True)):
        if data["type"] == "Person":
            orgs = find_co_mentioned_organizations(G, node_id)
            print(f"  {node_id} -> {orgs if orgs else 'no co-mentioned organizations'}")


if __name__ == "__main__":
    main()
