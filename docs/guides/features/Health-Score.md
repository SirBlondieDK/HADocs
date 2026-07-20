# Health Score

The Health Score summarizes the observed condition of a Home Assistant installation using explainable, normalized penalties. It is a prioritization aid, not an arbitrary percentage.

The score considers active affected entities, severity, maintenance findings, root cause complexity, installation size, and disabled entities. Disabled entities are not treated as active problems.

The **Potential Health Score** estimates the improvement available from addressing identified root causes. Score explanations show why points were lost and which actions can recover them.

Next: explore installation relationships with [Explorer](Explorer.md), or return to the [documentation home](../../README.md).
