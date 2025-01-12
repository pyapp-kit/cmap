# Changelog

## [v0.5.0](https://github.com/pyapp-kit/cmap/tree/v0.5.0) (2025-01-12)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.4.0...v0.5.0)

**Implemented enhancements:**

- feat: update for crameri v8 [\#83](https://github.com/pyapp-kit/cmap/pull/83) ([tlambert03](https://github.com/tlambert03))
- feat: Implement Google Earth Engine palette external [\#82](https://github.com/pyapp-kit/cmap/pull/82) ([SiggyF](https://github.com/SiggyF))
- feat: Add the pantanal colormap [\#81](https://github.com/pyapp-kit/cmap/pull/81) ([apcamargo](https://github.com/apcamargo))

**Merged pull requests:**

- ci\(dependabot\): bump codecov/codecov-action from 4 to 5 [\#78](https://github.com/pyapp-kit/cmap/pull/78) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(pre-commit.ci\): autoupdate [\#77](https://github.com/pyapp-kit/cmap/pull/77) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.4.0](https://github.com/pyapp-kit/cmap/tree/v0.4.0) (2024-11-01)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.3.0...v0.4.0)

**Implemented enhancements:**

- build: support py3.13 [\#76](https://github.com/pyapp-kit/cmap/pull/76) ([tlambert03](https://github.com/tlambert03))
- feat: add cmasher colormaps [\#75](https://github.com/pyapp-kit/cmap/pull/75) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs: add note about bang wong paper [\#72](https://github.com/pyapp-kit/cmap/pull/72) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- Rename tlambert03/cmap -\> pyapp-kit/cmap [\#73](https://github.com/pyapp-kit/cmap/pull/73) ([tlambert03](https://github.com/tlambert03))
- ci\(pre-commit.ci\): autoupdate [\#70](https://github.com/pyapp-kit/cmap/pull/70) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.3.0](https://github.com/pyapp-kit/cmap/tree/v0.3.0) (2024-07-24)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.2.2...v0.3.0)

**Implemented enhancements:**

- feat: Add the `cerrado` sequential colormap [\#69](https://github.com/pyapp-kit/cmap/pull/69) ([apcamargo](https://github.com/apcamargo))
- feat: add flexible integer conversion [\#68](https://github.com/pyapp-kit/cmap/pull/68) ([tlambert03](https://github.com/tlambert03))
- Add the `observable10` qualitative colormap [\#67](https://github.com/pyapp-kit/cmap/pull/67) ([apcamargo](https://github.com/apcamargo))
- feat: Add the `okabeito` namespace and colormap [\#65](https://github.com/pyapp-kit/cmap/pull/65) ([apcamargo](https://github.com/apcamargo))
- feat: Add the `araucaria` sequential colormap [\#64](https://github.com/pyapp-kit/cmap/pull/64) ([apcamargo](https://github.com/apcamargo))

**Documentation:**

- docs: add contrib namespace, add how-to-contribute to FAQ [\#63](https://github.com/pyapp-kit/cmap/pull/63) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- refactor: clarify that authors/license can be added directly to colormap entries, update contrib [\#66](https://github.com/pyapp-kit/cmap/pull/66) ([tlambert03](https://github.com/tlambert03))

## [v0.2.2](https://github.com/pyapp-kit/cmap/tree/v0.2.2) (2024-06-20)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.2.1...v0.2.2)

**Implemented enhancements:**

- feat: smaller serialization for catalog items [\#59](https://github.com/pyapp-kit/cmap/pull/59) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: fixes for numpy2 [\#60](https://github.com/pyapp-kit/cmap/pull/60) ([tlambert03](https://github.com/tlambert03))

## [v0.2.1](https://github.com/pyapp-kit/cmap/tree/v0.2.1) (2024-05-17)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.2.0...v0.2.1)

**Implemented enhancements:**

- Expose `Colormap.num_colors` and document usage for cycling through qualitative colormaps  [\#55](https://github.com/pyapp-kit/cmap/pull/55) ([andy-sweet](https://github.com/andy-sweet))

**Documentation:**

- docs: make colormap attributes more visible [\#56](https://github.com/pyapp-kit/cmap/pull/56) ([tlambert03](https://github.com/tlambert03))

## [v0.2.0](https://github.com/pyapp-kit/cmap/tree/v0.2.0) (2024-04-28)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.1.3...v0.2.0)

**Implemented enhancements:**

- feat: add shifted method [\#52](https://github.com/pyapp-kit/cmap/pull/52) ([tlambert03](https://github.com/tlambert03))
- feat: add over/under/bad colors [\#50](https://github.com/pyapp-kit/cmap/pull/50) ([tlambert03](https://github.com/tlambert03))
- feat: add Paul Tol's colormaps [\#48](https://github.com/pyapp-kit/cmap/pull/48) ([Jhsmit](https://github.com/Jhsmit))
- feat: add support for pyqtgraph [\#32](https://github.com/pyapp-kit/cmap/pull/32) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: fix interpolation argument preservation in custom colormaps [\#47](https://github.com/pyapp-kit/cmap/pull/47) ([tlambert03](https://github.com/tlambert03))
- fix: misc fixes for pydantic deprecations and other breakages [\#38](https://github.com/pyapp-kit/cmap/pull/38) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs: use natsort for docs [\#51](https://github.com/pyapp-kit/cmap/pull/51) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- ci\(dependabot\): bump softprops/action-gh-release from 1 to 2 [\#42](https://github.com/pyapp-kit/cmap/pull/42) ([dependabot[bot]](https://github.com/apps/dependabot))
- chore: use ruff instead of black [\#41](https://github.com/pyapp-kit/cmap/pull/41) ([tlambert03](https://github.com/tlambert03))
- test: Add test\_min extra and make sure tests run with bare minimum [\#40](https://github.com/pyapp-kit/cmap/pull/40) ([tlambert03](https://github.com/tlambert03))
- ci\(dependabot\): bump aganders3/headless-gui from 2.1 to 2.2 [\#37](https://github.com/pyapp-kit/cmap/pull/37) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump codecov/codecov-action from 3 to 4 [\#36](https://github.com/pyapp-kit/cmap/pull/36) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump actions/setup-python from 4 to 5 [\#34](https://github.com/pyapp-kit/cmap/pull/34) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump aganders3/headless-gui from 1.2 to 2.1 [\#33](https://github.com/pyapp-kit/cmap/pull/33) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.1.3](https://github.com/pyapp-kit/cmap/tree/v0.1.3) (2023-12-04)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.1.2...v0.1.3)

**Fixed bugs:**

- update to\_pygfx [\#31](https://github.com/pyapp-kit/cmap/pull/31) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- update docs and pre-commit [\#30](https://github.com/pyapp-kit/cmap/pull/30) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- ci\(dependabot\): bump styfle/cancel-workflow-action from 0.11.0 to 0.12.0 [\#28](https://github.com/pyapp-kit/cmap/pull/28) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.1.2](https://github.com/pyapp-kit/cmap/tree/v0.1.2) (2023-10-08)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.1.1...v0.1.2)

**Implemented enhancements:**

- feat: support python 3.12 [\#24](https://github.com/pyapp-kit/cmap/pull/24) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: fix for issues in mpl 3.8.0 [\#27](https://github.com/pyapp-kit/cmap/pull/27) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- ci\(pre-commit.ci\): autoupdate [\#26](https://github.com/pyapp-kit/cmap/pull/26) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.1.1](https://github.com/pyapp-kit/cmap/tree/v0.1.1) (2023-09-07)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.1.0...v0.1.1)

**Implemented enhancements:**

- feat: select unique names by category [\#25](https://github.com/pyapp-kit/cmap/pull/25) ([tlambert03](https://github.com/tlambert03))

## [v0.1.0](https://github.com/pyapp-kit/cmap/tree/v0.1.0) (2023-09-06)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.0.3...v0.1.0)

**Implemented enhancements:**

- feat: expose catalog as Colormap classmethod [\#22](https://github.com/pyapp-kit/cmap/pull/22) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: fix creating a cmap from existing cmap [\#21](https://github.com/pyapp-kit/cmap/pull/21) ([tlambert03](https://github.com/tlambert03))
- fix: change bwr to diverging [\#16](https://github.com/pyapp-kit/cmap/pull/16) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs: fix typos [\#23](https://github.com/pyapp-kit/cmap/pull/23) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- ci\(dependabot\): bump actions/checkout from 3 to 4 [\#20](https://github.com/pyapp-kit/cmap/pull/20) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.0.3](https://github.com/pyapp-kit/cmap/tree/v0.0.3) (2023-05-06)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.0.2...v0.0.3)

**Implemented enhancements:**

- feat: add colorcet aliases [\#11](https://github.com/pyapp-kit/cmap/pull/11) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs: break hue discontinuity in docs [\#13](https://github.com/pyapp-kit/cmap/pull/13) ([tlambert03](https://github.com/tlambert03))

## [v0.0.2](https://github.com/pyapp-kit/cmap/tree/v0.0.2) (2023-05-03)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/v0.0.1...v0.0.2)

**Implemented enhancements:**

- feat: add notebook repr with png encode [\#8](https://github.com/pyapp-kit/cmap/pull/8) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- Update README.md [\#9](https://github.com/pyapp-kit/cmap/pull/9) ([tlambert03](https://github.com/tlambert03))
- docs: fix links [\#6](https://github.com/pyapp-kit/cmap/pull/6) ([tlambert03](https://github.com/tlambert03))

## [v0.0.1](https://github.com/pyapp-kit/cmap/tree/v0.0.1) (2023-04-30)

[Full Changelog](https://github.com/pyapp-kit/cmap/compare/7d88f0329eb3b52faf0a63ae1ce207fe86455426...v0.0.1)

**Merged pull requests:**

- rearrange catalog structure [\#3](https://github.com/pyapp-kit/cmap/pull/3) ([tlambert03](https://github.com/tlambert03))
- ci\(dependabot\): bump codecov/codecov-action from 2 to 3 [\#2](https://github.com/pyapp-kit/cmap/pull/2) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump styfle/cancel-workflow-action from 0.9.1 to 0.11.0 [\#1](https://github.com/pyapp-kit/cmap/pull/1) ([dependabot[bot]](https://github.com/apps/dependabot))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
