import pytest

from src.part_b2 import NODES, TRIPLES, build_graph, find_co_mentioned_organizations


@pytest.fixture
def graph():
    return build_graph(NODES, TRIPLES)


def test_person_in_two_articles_gets_each_org_once(graph):
    """Raj is in a2 and a3; Contoso appears in both but is returned once."""
    assert find_co_mentioned_organizations(graph, "person:Raj Mehta") == [
        "org:Contoso Tech",
        "org:Fabrikam Capital",
    ]


def test_locations_are_not_returned_as_organizations(graph):
    """Article a1 also mentions Denver, a Location, which must not be returned."""
    assert find_co_mentioned_organizations(graph, "person:Maria Gomez") == [
        "org:Northwind Logistics"
    ]


def test_person_in_no_article_and_unknown_id_return_empty(graph):
    """Ana is mentioned nowhere; an unknown ID and a non-Person node also give []."""
    assert find_co_mentioned_organizations(graph, "person:Ana Silva") == []
    assert find_co_mentioned_organizations(graph, "person:Nobody") == []
    assert find_co_mentioned_organizations(graph, "org:Contoso Tech") == []


def test_triple_with_undeclared_node_raises():
    """A typo in a node ID fails loudly instead of creating an untyped node."""
    with pytest.raises(ValueError):
        build_graph(NODES, [("article:a1", "mentions", "person:Typo")])
