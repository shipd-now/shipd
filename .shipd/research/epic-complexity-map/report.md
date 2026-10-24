# Rubrics and maps for knowing when an epic is planned deep enough

> Prepared by the shipd research skill (/s:research).

## Summary

This report looks for existing UX and DX that rate a feature's complexity and show when planning has gone deep enough. The goal is to inform a rubric and a visual complexity map for `/s:epic-grill`. Today `/s:epic` rates each member low/medium/high on four axes (Code, Integration, Unknowns, Risk). `/s:plan` also picks a fast or depth path by counting five signals. Nothing yet ties those ratings to how hard the grill digs, or tells the grill when to stop.

The strongest prior art measures **unknowns, not size**. Shape Up's hill chart plots each scope from "unknown" to "known" to "done" and pushes the scariest work uphill first [1]. Shape Up's shaping stage hunts "rabbit holes" until the work is "as free of holes as possible" [2]. Liz Keogh's 1–5 scale rates who has done the work before, from "we all know how" to "nobody in the world has". She treats a 5 as a spike, not a plan [3][4]. These framings give a stop rule that size scores lack: stop digging when no uphill items remain.

AI planning tools already ship both halves of the idea. Task Master scores tasks 1–10 on five factors and expands those above a threshold into subtasks [5]. Spec Kit's `/clarify` rates ten coverage categories Clear, Partial, or Missing. It asks at most five questions, ranked by Impact × Uncertainty, and stops when critical gaps close [6]. For the map, CodeScene nests circles by folder and colours them by health [7]. Jira draws dependency tiles with red arrows for off-track links [8]. The warning from practice: a hard "definition of ready" gate drifts toward waterfall, so guidelines beat rules [9].

**Implication for shipd:** score each member on the existing four axes, plus a Keogh-style novelty level. Let the score set a question budget per member, and stop when every member is "downhill". Render the epic as a dependency graph whose nodes carry the score and the uphill/downhill state.

## Rubrics that rate unknowns rather than size

**Shape Up hill chart.** The hill chart is "a diagram showing the status of work on a spectrum from unknown to known to done" [1]. Uphill is the phase "where there are still unknowns or unsolved problems". Downhill is where "all unknowns are solved and only execution is left" [1]. Each dot is a scope, and "a dot that doesn't move is effectively a raised hand" [1]. The chart "motivates the team to push the scariest work uphill first" [1].

**Shape Up rabbit holes.** A rabbit hole is a "part of a project that is too unknown, complex, or open-ended to bet on" [2]. Shapers find them by walking "through a use case in slow motion". They ask "Does this require new technical work we've never done before?" [2]. They resolve each hole by patching it, cutting it, or declaring it "out of bounds" [2]. Well-shaped work "looks like a thin-tailed probability distribution" [2]. Shape Up rewrites "Is this possible?" as "is X possible in 6-weeks?", because "everything is possible but nothing is free" [2].

**Keogh's novelty scale.** Liz Keogh rates work by who has done it before [3]:

- 5: "Nobody in the world has ever done this before."
- 4: "Someone in the world did this, but not in our organization."
- 3: "Someone in our company has done this, or we have access to expertise."
- 2: "Someone in our team knows how to do this."
- 1: "We all know how to do this."

A 5 "is likely to be a spike, or an experiment of some kind" [3]. With scores in hand, "it's very easy to see where the risk is … and to do those aspects first" [3]. Her Cynefin mapping sets planning depth per level. Known work needs "a brief outline". Knowable work needs expert input. Novel work calls for trying "something out – safely, so that it's all right to fail" [4].

**Spikes as the escape hatch.** A spike uses "the simplest possible program to explore potential solutions" and gauges "how much work will be required" [10]. "Spikes should be timebound" [10]. For a planner, a spike marks the point where more questions stop paying off.

## How AI planning tools gate depth

**Task Master `analyze-complexity`.** It scores pending tasks 1–10 on technical complexity, time, dependency complexity, risk, and knowledge requirements [5]. Scores above 7 mean "expand", 5–7 mean "consider expanding", and below 5 mean no expansion [5]. Each high task gets reasoning, risk mitigations, and a suggested subtask count such as "Expand into 5-7 subtasks" [5]. The expand command then consumes the report [5]. The fetched page disagrees with itself: the `--threshold` default is 5, but the "high" band starts above 7 [5].

**Spec Kit `/clarify`.** It rates a spec against ten categories, such as Functional Scope, Data Model, Edge Cases, and Completion Signals. Each category is Clear, Partial, or Missing [6]. It asks at most five questions per session. When more than five categories are open, it picks the top five by "(Impact * Uncertainty)" [6]. It stops when critical ambiguities resolve, when the user says "done" or "stop", or at five questions [6]. Its closing summary marks each category Resolved, Deferred, Clear, or Outstanding [6]. That four-state summary already acts as a per-category "deep enough" report.

## Visual complexity maps

**CodeScene hotspot map.** The map is "interactive and hierarchical". "Each large blue circle represents a folder", and nested circles are hotspots [7]. "The lower the code health, the more red the corresponding circle" [7]. The priority signal comes from change frequency: "Red refactoring targets should be dealt with first" [7]. The pattern carries over to an epic: containment shows grouping, and colour shows risk.

**Jira dependencies view.** It "displays work items as tiles with arrows to illustrate which work items are dependent on others" [8]. It "only shows work items in your plan that have dependencies" [8]. "If the arrow turns red, this indicates that the dependency is off-track" [8]. Colour sits on the edge, not the node, so problem links stand out.

**Hill chart as a map.** The hill itself is a one-dimensional map of epistemic state, with a dot per scope [1]. It answers "are we done digging?" more directly than any size chart.

## Knowing when to stop

- **Stop rule from unknowns.** Shape Up's rule is concrete: plan until the work is "as free of holes as possible", with elements "defined enough and familiar enough" [2]. Spec Kit's rule is mechanical: stop when no Partial or Missing category has high impact [6].
- **Last responsible moment.** The Poppendiecks define it as "the moment at which failing to make a decision eliminates an important alternative" [11]. Deciding later than that means "decisions are made by default" [11]. A grill can defer any question that closes no option now.
- **Guidelines, not gates.** Mike Cohn warns that a definition of ready "becomes a huge step towards a sequential, stage-gate approach" [9]. He advises: "Favor guidelines rather than rules on your Definition of Ready" [9]. A complexity rubric should steer the question budget, not block a member outright.

## Gaps & caveats

- **No fetched source pairs a rubric with an epic-level map.** Task Master and Spec Kit score without a map, and CodeScene and Jira map without a planning score. Combining the two is untested design, not prior art.
- **Task Master's bands are internally inconsistent** in the fetched doc [5]. Its factor weights are not published.
- **Spec Kit's numbers come from a template**, not from measured outcomes [6]. Nothing shows that five questions is the right cap.
- **Rubric reliability is weak.** The earlier shipd report [Deciding which epic members can be planned in parallel](../parallel-planning-rubric/report.md) found low inter-rater agreement on judgement rubrics. Keep any summed score advisory.
- **Not fetched, so not cited:** the Stacey matrix, Jeff Patton's story maps, Kiro's EARS specs, and Linear's views. Search snippets touched them, but no primary page was read.

## Sources

1. Shape Up, Chapter 13: Show Progress (hill charts) — https://basecamp.com/shapeup/3.4-chapter-13
2. Shape Up, Chapter 5: Risks and Rabbit Holes — https://basecamp.com/shapeup/1.4-chapter-05
3. Liz Keogh, "Estimating Complexity" — https://lizkeogh.com/2013/07/21/estimating-complexity/
4. Liz Keogh, "Cynefin for Developers" — https://lizkeogh.com/cynefin-for-developers/
5. Task Master, analyze-complexity command — https://cdn.jsdelivr.net/npm/task-master-ai-notion@0.26.0/assets/claude/commands/tm/analyze-complexity/analyze-complexity.md
6. GitHub Spec Kit, clarify command template — https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md
7. CodeScene, Hotspots and technical debt — https://codescene.io/docs/guides/technical/hotspots.html
8. Atlassian, What is the dependencies view in your plan? — https://support.atlassian.com/jira-software-cloud/docs/what-is-the-dependencies-report-in-advanced-roadmaps/
9. Mike Cohn, "The Dangers of a Definition of Ready" — https://www.mountaingoatsoftware.com/blog/the-dangers-of-a-definition-of-ready
10. Wikipedia, Spike (software development) — https://en.wikipedia.org/wiki/Spike_(software_development)
11. Jeff Atwood, "The Last Responsible Moment" — https://blog.codinghorror.com/the-last-responsible-moment/
