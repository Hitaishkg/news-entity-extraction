# News Article Entity Extraction

Take-home assignment: clean a small article list and count articles per topic
per week (Part A); evaluate an LLM's entity extraction (Part B1); model articles
and entities as a graph and query it (Part B2).


## Part A: cleaning and weekly counts

Code: `src/part_a.py`. Data: `data/articles.json` (the five rows from the brief).

Result:

| Week starting | ISO week | Topic | Count |
|---|---|---|---|
| 2026-07-27 | 2026-W31 | local | 1 |
| 2026-08-03 | 2026-W32 | business | 2 |
| 2026-08-03 | 2026-W32 | sports | 1 |

One duplicate was removed (the second "City Council Approves New Transit Line").

### Decisions and assumptions

- **Duplicates:** two rows are the same article when the title (trimmed,
  case-insensitive) and the parsed date match. I keep the first occurrence.
  Title-only matching would follow the brief literally but could merge different
  articles that share a title on different days.
- **Ambiguous date:** `08/01/2026` could be 1 August or 8 January. I read slash
  dates as MM/DD/YYYY because the same article appears with the ISO date
  2026-08-01. A day-first date such as `13/01/2026` fails this format and is
  reported rather than silently misread. With real data I'd confirm the source's
  format instead of inferring it.
- **Calendar week:** ISO 8601 weeks (Monday start), labelled by ISO year and
  week. 9 August 2026 is a Sunday, so it falls in the same week as 3 August; with
  Sunday-start weeks it would be counted in the following week.
- **Bad rows:** rows with an unparseable or missing date, or no title, are
  skipped and reported with a reason instead of stopping the run. A missing topic
  becomes "unknown" so the article is still counted.
- **Topics** are lowercased ("Local" and "local" are the same topic).

## Part B1: Evaluating the extraction

Each entity is scored as a (type, text) pair. Strict matching needs both the
type and the text to match; lenient matching compares text only.

| Scope | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Overall (strict) | 2 | 1 | 1 | 0.67 | 0.67 | 0.67 |
| Overall (lenient, text only) | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Person | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Organization | 1 | 1 | 0 | 0.50 | 1.00 | 0.67 |
| Location | 0 | 0 | 1 | undefined (no predictions) | 0.00 | 0.00 |

Location precision is 0/0. I report it as undefined; in any average I'd treat
it as 0.


Which errors matter more. The one real error is that Denver was labelled an organization instead of a location. Under strict matching this counts twice, as a false positive and a false negative, while the lenient, text-only score is perfect: the model found every entity and mislabelled one. For a knowledge graph, a wrong type is worse than a missed entity because it fails silently. A missed entity leaves a gap. A wrong type creates a fact that looks valid but is false. If this extraction were loaded into the graph, Denver would become an Organization node, the locatedIn edge would have no Location to point to, and the B2 query “organizations mentioned with Maria Gomez” would wrongly return Denver.

The reference itself is debatable. “Partnership with the city of Denver” refers to the city government, which acts like an organization, so the model’s label is defensible. I’d resolve this with a labelling rule, used in both the reference guidelines and the extraction prompt: use the literal reading (Denver is a location) unless the sentence explicitly treats the entity as an organization, for example “Denver’s city council”.

## Part B2: graph model and query

Code: `src/part_b2.py`.

**Model.** A directed graph (NetworkX `DiGraph`). Each node has a `type`
(Article, Person, Organization, Location) and each edge has a `relation`:

- Person `worksAt` Organization
- Organization `locatedIn` Location
- Article `mentions` Person / Organization / Location

Node IDs are prefixed by type (`org:...`, `loc:...`), so the same name with two
types, like Denver in B1, can never collide. The graph is loaded from a list of
(subject, relation, object) triples, the same shape RDF uses.

**Data.** The articles in the brief have no entities, so the graph uses a small
sample set constructed for this exercise. The Maria Gomez article uses the B1
reference labels. I also added `mentions` edges to locations (beyond the brief's
Person/Organization) so the query can be tested to ignore them.

**Query.** `find_co_mentioned_organizations(graph, person_id)` takes two hops:
the articles that mention the person, then the organizations those articles
mention. It returns sorted IDs without duplicates, and `[]` for an unknown or
non-Person ID.

| Person | Co-mentioned organizations |
|---|---|
| Maria Gomez | Northwind Logistics |
| Raj Mehta | Contoso Tech, Fabrikam Capital |
| Ana Silva | (none) |

**Why NetworkX:** an in-memory graph keeps the repo runnable with one install.
In production I'd use a graph database.

## Tests

`tests/test_part_a.py` covers the month-first date reading, case-insensitive
dedup, the Sunday/ISO-week boundary and the full assignment data.
`tests/test_part_b2.py` covers duplicate organizations, location filtering,
unknown people and undeclared nodes.