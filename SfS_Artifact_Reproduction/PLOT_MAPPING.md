# Paper plot → artifact data mapping

## Figure 3 — No-attack 
`data/no_attack/thv_XXXX.xlsx`

## Figures 4–7 — Seconds-scale replay
`data/replay_seconds/thv_XXXX/delay_1s.xlsx` through `delay_5s.xlsx`

- Fig. 4: aggregate confusion counts across the five delay runs.
- Fig. 5: per-delay ROC.
- Fig. 6: per-delay TNR + cumulative TPR.
- Fig. 7: weighted score from each per-delay TPR/TNR pair.

## Figures 8–10 — Millisecond-scale replay
`data/replay_milliseconds/thv_XXXX/delay_100ms.xlsx`, `300ms`, `500ms`, `700ms`, `900ms`

- Fig. 8: per-delay ROC.
- Fig. 9: weighted score.
- Fig. 10: per-delay TNR + cumulative TPR.

## Figure 11 — replay at ms scale and sec one
Milliseconds:
`data/permutation_aware/milliseconds/delay_{500,700,900}ms/thv_XXXX.xlsx`

Seconds:
`data/permutation_aware/seconds/delay_{1,2,3,4,5}s/thv_XXXX.xlsx`

