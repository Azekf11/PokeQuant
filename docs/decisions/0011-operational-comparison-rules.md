# 0011 — Operational rules for strategy comparisons

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Refines: protocol §6.3, §7.0, §7.0b (`prereg-v1`) and
  [research/experiments/main.yaml](../../research/experiments/main.yaml) (`prereg-v2`)

## Context

Week S7 turns the pre-registered estimands and decision rules into code. Some
rules need details that the protocol leaves open: how a "ranking" is read
from posterior draws, what "decisive at the posterior mean" means for a
single model, and which metric decides H4. These details are fixed here,
**before the comparator is run on prices**; no economic result existed when
this record was written. None of them changes a pre-registered quantity.

## Decision

**Strategies and values.**

1. Values follow `valuation.py`: TCGplayer market price at t0. Missing prices
   are handled by the scenario's rule: pool median for central, zero for
   adverse. The gross scenario uses the central rule.
2. Strategy B (E1) buys each printing at most once, among the printings a pack
   can contain that have an *observed* price. It buys them in decreasing
   order of a(c), skipping any that exceeds the remaining budget n·b. Its
   profit is Π_B = Σ [l(c) − a(c)]. It does not depend on pull rates and is
   the same in every epistemic draw.
3. E2 targets are chosen among printings a pack can contain that have an
   observed price. `top_price` is the one with the highest a(c);
   `top_sir` is the Special Illustration Rare with the highest a(c). Because
   a(c) is increasing in p(c), the choice is the same in every scenario.
   Strategy B buys the target, so Π_B = 0 exactly; for A,
   Π = a(c*) − K_net.
4. Scenarios share their random numbers (common random numbers). The same
   posterior draws and the same simulated openings are valued under each cost
   scenario, so differences between scenarios carry no sampling noise from
   separate simulations.

**Reading the comparisons.**

5. Each metric has a direction. Higher is better for mean, median, quantiles
   and P(Π > 0). Lower is better for P(loss), VaR 5 % and CVaR 5 %. "A beats
   B" in a draw means strictly better, so ties count against A. The verdict is
   the §7.0b rule on the share of draws: decisive at ≥ 0.90 either way,
   otherwise undetermined.
6. **H1** is supported if both of the following happen in one set, scenario
   and budget or target:
   - the verdict on the mean is decisive for one strategy;
   - the verdict on the median or on CVaR 5 % is decisive for the other.

   H1 is also supported if, for Strategy A, Π has a mean > 0 and a P(loss) > 0.5
   in at least 90 % of draws.
7. **H2.** A comparison is "decisive at the posterior mean" if, in a separate
   run at the posterior-mean model, |metric_A − metric_B| exceeds three Monte
   Carlo standard errors. The metrics considered are mean, median, P(loss) and
   CVaR 5 %. H2 is supported if one such comparison becomes undetermined, or
   decisive for the other strategy, under posterior draws.
8. **H3.** For each draw, the change is computed as follows:
   - E1: (mean_A − Π_B) under gross minus the same under central;
   - E2: P(Π > 0) under gross minus the same under central.

   H3 is supported if, for at least one set and budget or target, the
   2.5 %–97.5 % interval of this change over draws lies strictly above 0. The
   adverse scenario is reported but does not decide H3.
9. **H4** uses the verdict on the mean in the central scenario. It is
   supported if the decisive winner differs between two sets for the same
   budget or target type. The second price snapshot (2026-12-13) is not yet
   available. Until it is, the date half of H4 is reported as pending, and H4
   is decided on sets only.
10. A comparison where both strategies have an identical metric in every draw
    is reported as "tie", not as a verdict.

**Reporting.** All verdicts, including those that do not support a
hypothesis, are reported in `research/reports/results.md`. The run writes
JSON and CSV results under `results/<run_id>/` with its manifest.
