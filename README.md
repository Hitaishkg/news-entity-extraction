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


Which errors matter more. The one real error is that Denver was labelled an organization instead of a location. Under strict matching this counts twice, as a false positive and a false negative, while the lenient, text-only score is perfect: the model found every entity and mislabelled one. For a knowledge graph, a wrong type is worse than a missed entity because it fails silently. A missed entity leaves a gap. A wrong type creates a fact that looks valid but is false: Denver becomes an Organization node, the locatedIn edge has no Location to point to, and the B2 query “organizations mentioned with Maria Gomez” would wrongly return Denver.

The reference itself is debatable. “Partnership with the city of Denver” refers to the city government, which acts like an organization, so the model’s label is defensible. I’d resolve this with a labelling rule, used in both the reference guidelines and the extraction prompt: use the literal reading (Denver is a location) unless the sentence explicitly treats the entity as an organization, for example “Denver’s city council”.