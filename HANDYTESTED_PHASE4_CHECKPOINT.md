# HandyTested Phase 4 checkpoint (2026-09-20)

This is an execution checkpoint, not a final completion claim. Read the Phase 4 request and `HANDYTESTED_PHASE4_REPORT.md` before resuming. Do not redo the nine completed articles unless live QA reveals a regression.

## Completed and published

All nine kept their original slug/self-canonical, gained a research-led English article and exact Amazon Associate disclosure, reduced model-specific tagged Amazon searches, source record, revision-guarded dry-run, pre-write backup, WordPress/Rank Math update and live-public release checks. No direct ASIN was invented.

| Article | Post ID | Apply run / backup artifact name |
|---|---:|---|
| Heat guns | 56 | https://github.com/HeberPython/agente-sites/actions/runs/35532249566 / `handytested-phase4-heat-backup` |
| Multimeters | 53 | https://github.com/HeberPython/agente-sites/actions/runs/35532808506 / `handytested-phase4-multimeter-backup` |
| Smart home hubs | 41 | https://github.com/HeberPython/agente-sites/actions/runs/35533252530 / `handytested-phase4-smart-hubs-backup` |
| Wireless earbuds under $100 | 25 | https://github.com/HeberPython/agente-sites/actions/runs/35533550235 / `handytested-phase4-earbuds-backup` |
| Drill presses | 69 | https://github.com/HeberPython/agente-sites/actions/runs/35533895758 / `handytested-phase4-drill-backup` |
| Random orbital sanders | 37 | https://github.com/HeberPython/agente-sites/actions/runs/35534278964 / `handytested-phase4-sanders-backup` |
| Voltage testers | 50 | https://github.com/HeberPython/agente-sites/actions/runs/35534500319 / `handytested-phase4-voltage-backup` |
| Pet-hair robot vacuums | 187 | https://github.com/HeberPython/agente-sites/actions/runs/35534871362 / `handytested-phase4-robot-backup` |
| Indoor hydroponic gardens | 185 | https://github.com/HeberPython/agente-sites/actions/runs/35536998302 / `handytested-phase4-hydroponics-backup` (artifact ID 10612992040) |

WordPress original-post backup artifacts are attached to those apply runs and retained for 30 days. Random orbital sanders had an initial failed apply (run `35534136103`) because an unrelated related-guide fetch timed out; its rollback restored the prior post, a second dry-run `35534259258` passed, and the successful apply is the one above.

## Next article and batch

**NEXT ARTICLE:** `best-portable-outdoor-grills-under-300-for-2025` (P1), then follow the exact P1 and P2 order in `HANDYTESTED_PHASE3_REPORT.md`. Seven P0 and two P1 are complete; 21 P1 and 7 P2 remain. None of those 28 has been researched or published in Phase 4 yet. Do not mark them genuinely blocked merely because Phase 3 worksheets said "Screened; blocked".

## Research already obtained for next work

The hydroponic guide's three exact products, manufacturer evidence and Click & Grow method exclusion are in `handytested_sources/best-indoor-hydroponic-gardening-systems-under-300.md`. For pet-hair vacuums, sources and exclusions are in `handytested_sources/best-robot-vacuums-for-pet-hair-under-300.md`; no need to revisit unless availability changes. Each completed article's source record names its primary manufacturer/manual evidence.

## Outstanding cross-cutting issues

- Amazon CTAs are specific tagged searches, not verified direct product links. SiteStripe/ASIN verification remains pending; absence of a direct link does not block textual correction.
- Existing featured-image licensing/product match is unverified. Never assert usage rights without evidence.
- Mobile QA found the article comparison tables scroll inside narrow wrappers. Document-level overflow comes from injected AdSense `aswift_*` iframe hosts: 718 px on the voltage article and 1200 px on the robot-vacuum article at a 320 px viewport. Preserve AdSense and handle as a separate account/site-layout item.
- Rank Math sitemap, global Astra CSS/footer, Pinterest diagnostics, Search Console and AdSense settings remain the previously recorded admin/configuration issues. They are not blockers for article work.
- GitHub Actions emits Node 20 deprecation and upcoming Ubuntu label warnings; neither failed these releases.
- Unrelated pre-existing untracked `astra.zip`, `astra_theme/`, `ht_install_astra.php` are user files. Do not alter them.

## Resume instruction

In `C:\Users\Heber\agente-sites` on `main`, read `git status --short` and this checkpoint; start public-source research for `best-portable-outdoor-grills-under-300-for-2025`. For each article: read snapshot and source record, research current exact models, write original English copy plus source evidence, validate locally, stage only task files, commit/push, run its GitHub Actions dry-run, apply with backup, check live, update report/checkpoint, and immediately proceed to the next. Do not publish an article when its snapshot/revision guard fails; investigate that specific article and continue others. Do not return a plan in place of execution.
