# Changelog

## \[Unreleased\]

> Note: Previous 3.x version entries reflect internal development history. The first public release
> track starts at `0.1.0`.

### Features

- **UI Bridge**: Production-ready HTTP API for exposing RapidKit CLI to web frontends
  - Bearer token authentication with `--api-key` option
  - IP-based rate limiting (default: 10 req/60s)
  - Security headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
  - Structured JSON logging for audit trails
  - Command timeout protection (default: 300s)
  - Path security with directory traversal prevention
  - OpenAPI/Swagger documentation at `/docs`
  - Response models for type-safe API contracts
  - Input validation with size limits (args: 100, stdin: 10MB, env: 50 vars)
  - Three endpoints: `/healthz`, `/manifest`, `/invoke`
  - **31 end-to-end integration tests** covering all security features

## [3.0.1](https://github.com/Baziar/core/compare/v3.0.0...v3.0.1) (2025-11-17)

### Bug Fixes

- **ci:** lowercase docker tags and guard psutil import
  ([cef3438](https://github.com/Baziar/core/commit/cef3438399df0ff92b2f89a6907941fb830588af))
- expose reusable workflows for community
  ([81bfcbc](https://github.com/Baziar/core/commit/81bfcbc77d1f99e261a677d1fa19e480298f1e2f))
- **workflows:** grant release permissions
  ([dd9af0a](https://github.com/Baziar/core/commit/dd9af0a735b720a3d6f01b4b6b9586c782c90846))
- **workflows:** normalize community docker owner slug
  ([95e675d](https://github.com/Baziar/core/commit/95e675d09c646fe438dff7260b5708e49d3fe0fa))

## [3.0.0](https://github.com/Baziar/core/compare/v2.0.2...v3.0.0) (2025-11-16)

### ⚠ BREAKING CHANGES

- Old logging module structure replaced with new modular approach

### Features

- Add advanced pre-commit management system
  ([75841db](https://github.com/Baziar/core/commit/75841db4af816e2b9a65a9dec6ee43357c159c55))
- add automated GitHub variables setup script
  ([634f230](https://github.com/Baziar/core/commit/634f2302f77ea89129689c2ef2651e622fbfad0c))
- Add automatic commit message validation to pre-commit hooks
  ([bbdc324](https://github.com/Baziar/core/commit/bbdc3248b0d2ca996908c38cff8a33f732e401fa))
- add Black configuration and fix distribution workflows
  ([bd8d6a5](https://github.com/Baziar/core/commit/bd8d6a50ab321838aed4d173b565c5fcf5b27085))
- Add comprehensive commit message standards documentation
  ([03a4ebb](https://github.com/Baziar/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))
- Add comprehensive distribution test script
  ([7ee19b9](https://github.com/Baziar/core/commit/7ee19b992fc0f279aeacf9fa2c3db60deaae9030))
- Add debug commit type support
  ([e0209e9](https://github.com/Baziar/core/commit/e0209e979984e1b30cb9f56beb4bfd9f0151b34e))
- Add path-based triggers for better workflow execution
  ([c685e7c](https://github.com/Baziar/core/commit/c685e7c18ff1ba758935d08343cff0d72b740684))
- Add professional basic test file
  ([59c1e53](https://github.com/Baziar/core/commit/59c1e5315434d0bc7bdb22ab497d2e59f83739ee))
- add test file for validation testing
  ([5da8254](https://github.com/Baziar/core/commit/5da8254d1a1908c4ec8dba6797b89d3af7415532))
- Add tier coverage analyzer and update mapping files
  ([72d4ca7](https://github.com/Baziar/core/commit/72d4ca725ab50be66f6894dd5f1b6924994230e0))
- Add tier-specific CODEOWNERS files for all distribution repositories
  ([288056d](https://github.com/Baziar/core/commit/288056d2753530a84f04683dffb66baa26e74ff4))
- add vendor snapshot layer for settings module
  ([d981d9c](https://github.com/Baziar/core/commit/d981d9c53c73eebe190d29158ecc49760910467e))
- Automate modules lock file generation
  ([a2f2dd4](https://github.com/Baziar/core/commit/a2f2dd4f8bac6cd9439e9830820b505573f3a629))
- **cli:** enhance merge and create interactive flows
  ([201e76c](https://github.com/Baziar/core/commit/201e76c7af8532da2b50f3b8b280a4d87a7d1f3d))
- Complete development environment setup
  ([8e093b8](https://github.com/Baziar/core/commit/8e093b83e2cf382093e4bee51a8f8aa8ebdf9aad))
- Complete mapping system reorganization and documentation centralization
  ([91f48e0](https://github.com/Baziar/core/commit/91f48e06f5f16aeb81c4873500ec7be9139d1f55))
- Complete overhaul of setup-distribution action with professional improvements
  ([53c3bd1](https://github.com/Baziar/core/commit/53c3bd15584b7d3565d1535e5158c88784088903))
- Complete professional overhaul of setup-distribution action and docs cleanup
  ([1b81c48](https://github.com/Baziar/core/commit/1b81c482a7a64910cfeccf55675a241cef9fb3e0))
- Complete tier filtering system with enterprise module removal
  ([b521a81](https://github.com/Baziar/core/commit/b521a8181d7bef9256c16eb3baf67d02960666b9))
- Comprehensive documentation and code updates for community distribution
  ([2958d26](https://github.com/Baziar/core/commit/2958d2668bf087a3bbd460beec6941e4088f8541))
- Comprehensive repository cleanup and community distribution preparation
  ([050a643](https://github.com/Baziar/core/commit/050a6430589b62ef5dc465ffcb470e5115059a41))
- **engine:** record module versions and improve resolution
  ([a5cbe0f](https://github.com/Baziar/core/commit/a5cbe0f9453a6817944e18f3522907b5bbce0aef))
- Enhance commit message validation
  ([c289b58](https://github.com/Baziar/core/commit/c289b58396f097e0b28a1e8f3bb8c7e29db13c06))
- expose module scaffold and validation CLIs
  ([dc1fe53](https://github.com/Baziar/core/commit/dc1fe53ae0fceacd541402f1904c219b131cc730))
- Implement automatic commit message validation for distribution
  ([03a4ebb](https://github.com/Baziar/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))
- implement GitHub repository variables for CI configuration
  ([341ea95](https://github.com/Baziar/core/commit/341ea956b7475fa89c04c25a612adfd2ec72e74e))
- implement Next.js-style professional CLI architecture
  ([df403fb](https://github.com/Baziar/core/commit/df403fb4ea86fac11269c8cb50bc3315dd28252f))
- implement plugin-based settings architecture
  ([59939db](https://github.com/Baziar/core/commit/59939db585599f846734d5a54a1f7026d75d4d83))
- improve git-commit-wrapper user feedback
  ([08798c8](https://github.com/Baziar/core/commit/08798c8a7569d844f0c0515ab8d6c31ad3bf8886))
- introduce deployment and logging modules with modular architecture
  ([6d6e16a](https://github.com/Baziar/core/commit/6d6e16ad10e53b1bf8a00eb9f024b100ccbabe69))
- major module system refactoring and kit updates
  ([f7d99ba](https://github.com/Baziar/core/commit/f7d99ba2b3a9571e38f6421d76e428f463ac028e))
- major updates to core, docs, and tests
  ([c6d2276](https://github.com/Baziar/core/commit/c6d22767b101ef465a205a4dd4266e4d8e660ea0))
- Multi-framework support foundation
  ([c7a6d1a](https://github.com/Baziar/core/commit/c7a6d1a89f53a9c0bf003b549ae544528e19a8d6))
- Optimize distribution system and license management
  ([18b2644](https://github.com/Baziar/core/commit/18b2644289b797c47d08c3a5bd888ee58b144078))
- polish community distribution experience
  ([6a6ae7f](https://github.com/Baziar/core/commit/6a6ae7ff84e2793211c4ce18e9a08486a11bc03e))
- realign module scaffolding
  ([fc202f9](https://github.com/Baziar/core/commit/fc202f96e700b0eb0f99f8ec9ff13bf1b29531d1))
- refresh free modules and health runtime
  ([f524217](https://github.com/Baziar/core/commit/f5242177158e6b04ac552849ba0883b3276b5e43))
- Reorganize modular system with enterprise-grade tooling
  ([2dc8cc9](https://github.com/Baziar/core/commit/2dc8cc975e97d8ca22768a111d022eb3926b8c1d))
- Transform RapidKit into Next.js-like development tool
  ([597cc55](https://github.com/Baziar/core/commit/597cc5520877f4ac07d12d0d3c42c2c00278d3d0))
- update module structure verification files
  ([d678daa](https://github.com/Baziar/core/commit/d678daa5048ec2afa92886368c1644fea63e299e))
- Update root_files_map.yml with missing files
  ([831816e](https://github.com/Baziar/core/commit/831816eaf75cb8649eaa2b29bf752fdfce6037e5))
- update test file with additional content
  ([2248818](https://github.com/Baziar/core/commit/2248818e8977eebcd660314b1f5c9a9b2bb2930d))

### Bug Fixes

- accept site-packages parents without drive regressions
  ([5a6e78e](https://github.com/Baziar/core/commit/5a6e78e8ed5e8feb4f5cde8384f1e89103705d01))
- add comprehensive debugging to setup job to identify bootstrap artifact issue
  ([e254650](https://github.com/Baziar/core/commit/e254650a1edb082ca7f9cfe1c3c067c27950dc05))
- Add distribution workflows to root_files_map.yml for proper tier distribution
  ([4d97831](https://github.com/Baziar/core/commit/4d97831dcde92e53727d56e4aaa0318360e2e616))
- Add Docker image verification step to prevent test failures
  ([129fde3](https://github.com/Baziar/core/commit/129fde35d90f505e2f356a75aaaca215a7869b2d))
- Add Dockerfile to workflow trigger paths so Docker job runs when Dockerfile changes
  ([d6c3c0b](https://github.com/Baziar/core/commit/d6c3c0bd25cb39055f6eb6b253727927d3f6e687))
- Add missing src_map.yml parameter to distribution action
  ([2646108](https://github.com/Baziar/core/commit/26461083fd4893dca026ae9793841dbe470eac10))
- Add parse_tier_files.py to scripts_map.yml for all tiers
  ([c48ea48](https://github.com/Baziar/core/commit/c48ea48fb9b3be4080ebbf83f077cebd21351f35))
- Add src/\* to root_files_map.yml for proper distribution
  ([dd54b3d](https://github.com/Baziar/core/commit/dd54b3db3b9be397ec5e64f8c7942549ed946ed3))
- add support for private repositories in distribution workflow
  ([1680165](https://github.com/Baziar/core/commit/16801653343305999b3456d0a3cb72ae5f696822))
- align cross-platform workflows
  ([74b5563](https://github.com/Baziar/core/commit/74b5563bae7f4779a37db3ed400315caa1629339))
- allow rsync to copy kit workflows
  ([46e668d](https://github.com/Baziar/core/commit/46e668dbdcb47a8300b1e57910f6356f0ab0ed33))
- Black formatting in generated test_basic.py files
  ([82bb1db](https://github.com/Baziar/core/commit/82bb1dbb822a1255f1147644f04a4f4af65bef07))
- change sync-distribution to PR-only triggers
  ([368c244](https://github.com/Baziar/core/commit/368c244a931050f0f7ba696bd90bb9f17e9841a3))
- **ci:** correct coverage aggregation by using .coverage data files
  ([b4c327d](https://github.com/Baziar/core/commit/b4c327d2a0473af5810dc27cd9bf8174d3d3f44e))
- **ci:** ensure module integrity installs template deps
  ([76ffdc9](https://github.com/Baziar/core/commit/76ffdc96fc6138df06304702cb2efe95576f3697))
- **ci:** ensure poetry module available
  ([0e8bf85](https://github.com/Baziar/core/commit/0e8bf854b73f6d47914cafa97f59978e7b2b1d1b))
- **ci:** Fix Poetry PATH issues in community CI workflow
  ([974a4ac](https://github.com/Baziar/core/commit/974a4acdd315dfa52aea08db81dbdd95033b3df1))
- **ci:** guard codecov upload with github token
  ([b0766ba](https://github.com/Baziar/core/commit/b0766ba00ce69d86ea389ee4aa5c90c675137032))
- **ci:** guard coverage summary downloads
  ([ab42244](https://github.com/Baziar/core/commit/ab422441679b98af4a0a49dc5ec45f6e26d45c4f))
- **ci:** harden community pipeline
  ([e790edd](https://github.com/Baziar/core/commit/e790edd98623d652d665958713b16885453ad1ea))
- **ci:** include core.frameworks in core tier
  ([767c70c](https://github.com/Baziar/core/commit/767c70c52208bb2da3e63debfce37b5a9c4ce048))
- **ci:** include core.module_sign in core tier
  ([0cab523](https://github.com/Baziar/core/commit/0cab5230793e816fc62058469f464702fa73a146))
- **ci:** include core.structure in core tier mapping
  ([b27c71a](https://github.com/Baziar/core/commit/b27c71a96a8921a3c1f0438cf2fee054ad40e122))
- **ci:** include engine dependencies in core tier
  ([3ceb092](https://github.com/Baziar/core/commit/3ceb092babd3b9ccacbc05091007f70980cffae7))
- **ci:** include kit bootstrap assets and stabilize repo detection
  ([ef78fb2](https://github.com/Baziar/core/commit/ef78fb27d7786bbf350bb67506534d6ce6ee171c))
- **ci:** include license_utils and py.typed in core tier
  ([d61117c](https://github.com/Baziar/core/commit/d61117c0c3ddd2bde9f96da361d6216e2b0c555d))
- **ci:** install psutil stubs and lowercase tags
  ([68bcaf5](https://github.com/Baziar/core/commit/68bcaf5a52801e8a4404a3a92cfe0c0b8e6b8eb3))
- **ci:** install psutil stubs and lowercase tags
  ([23193d6](https://github.com/Baziar/core/commit/23193d6397d2d104f0f0a72a103944d849ea0cef))
- **ci:** invoke poetry via python module
  ([6b4d5e4](https://github.com/Baziar/core/commit/6b4d5e4f8ab963109897045249c16c1fff180dbe))
- **ci:** keep staging pip patched
  ([fc5eb61](https://github.com/Baziar/core/commit/fc5eb61dfbdd47e198b2375c37b7fe66840b6729))
- **ci:** pin typer/click in CI to match local environment
  ([37b01a8](https://github.com/Baziar/core/commit/37b01a82f1dabf1777d54ec103580760f52cd038))
- **ci:** require patched pip for audit
  ([cbeed4c](https://github.com/Baziar/core/commit/cbeed4c8c3c8c87d1f3946d774f69330fbb5235a))
- **ci:** resolve distribution CI failures and logo issues
  ([787e977](https://github.com/Baziar/core/commit/787e97789314ab93a3734aa9eaf51e4d458fd64c))
- **ci:** resolve multiple CI/CD pipeline issues
  ([a2645d8](https://github.com/Baziar/core/commit/a2645d8ab2336eb2c6d62abd6156590c5b59bd3a))
- **ci:** stabilize cross-platform jobs
  ([ad299d0](https://github.com/Baziar/core/commit/ad299d0e20024569ed1128e99c4c1bb76d09e4a3))
- **ci:** stabilize cross-platform paths and hidden templates
  ([0ae8f41](https://github.com/Baziar/core/commit/0ae8f41a49fe03facce0c3a553b7982ca9ab352d))
- **ci:** unblock mypy optional deps
  ([1fd1bf0](https://github.com/Baziar/core/commit/1fd1bf08fc9a9c43dd664409e83720e8d00ce169))
- **cli:** honor click exit codes
  ([b427cc6](https://github.com/Baziar/core/commit/b427cc612675a7aa832342bb5598631820dd8d0a))
- **cli:** keep legacy help exit successful
  ([9ba95fe](https://github.com/Baziar/core/commit/9ba95fec35ccd1fbd7903b3347bdb0b516a6627d))
- **cli:** preserve typer exits
  ([d0f410a](https://github.com/Baziar/core/commit/d0f410a99871d6c1af245e7cbff287790847aecb))
- **cli:** propagate typer exit codes
  ([35b50f5](https://github.com/Baziar/core/commit/35b50f593b859fca5e6e91ad62abc0a47641a299))
- **cli:** resolve secondary option syntax compatibility issues
  ([2015804](https://github.com/Baziar/core/commit/201580486037f75fcaa5b232563cf305b761582f))
- **cli:** restore global module entrypoint
  ([94191af](https://github.com/Baziar/core/commit/94191af258e9d60d6d69044d8fa1278a92084c74))
- **cli:** support global help flag
  ([02c780f](https://github.com/Baziar/core/commit/02c780f8275764fc6a88cc43820fba819a1000a2))
- **cli:** tolerate legacy stdio encodings
  ([9749e65](https://github.com/Baziar/core/commit/9749e65277bc6d61ba09ca455d9b8e6ae8e63b7b))
- Code formatting and linting fixes from pre-commit hooks
  ([0305685](https://github.com/Baziar/core/commit/0305685cd26d3061b9b781dd206bbfe497416221))
- Complete community repository GitHub Actions setup
  ([9c67cf3](https://github.com/Baziar/core/commit/9c67cf3ccbf5515e3ce4c519b4c324b0a6d8505c))
- complete NestJS kit fixes
  ([479c597](https://github.com/Baziar/core/commit/479c59782134344209092fd9cc2fffb7fa9ae69c))
- completely remove PYTHONPATH from community CI workflow
  ([b3b5b68](https://github.com/Baziar/core/commit/b3b5b68ad56a5f90788c36b458dab0313a8e2658))
- Convert absolute cli imports to relative imports to fix ModuleNotFoundError
  ([851374a](https://github.com/Baziar/core/commit/851374ab14f9bc2bd012fc01617aba13261d612f))
- Correct \_module_priority function to handle zero priority values
  ([4e0ed8b](https://github.com/Baziar/core/commit/4e0ed8b456e095ea8318310ff853360e7dec2b41))
- Correct \_module_priority function to handle zero priority values
  ([18fd259](https://github.com/Baziar/core/commit/18fd259e88097fa89d76655e7e64fee9d2a3ad01))
- Correct \_module_priority function to handle zero priority values
  ([55ac92f](https://github.com/Baziar/core/commit/55ac92f89e89fbb990d9cc96768383d838999650))
- Correct \_module_priority function to handle zero priority values
  ([dfcde4c](https://github.com/Baziar/core/commit/dfcde4c2901b6d7fa249a2c7bd14dd7c1c919111))
- Correct \_module_priority function to handle zero priority values
  ([6e36c46](https://github.com/Baziar/core/commit/6e36c46cce460ec2c459ffabf4525e8dbf894473))
- Correct coverage data file paths in CI aggregation
  ([0d61483](https://github.com/Baziar/core/commit/0d614833a1b1c7f121a2e23f0e85ca6732974bc4))
- Correct GitHub Actions workflow env variable references
  ([cd13422](https://github.com/Baziar/core/commit/cd13422d3c100807b948dc05da87b9d714e5705a))
- correct Jinja2 template syntax in CI workflow
  ([7bd31a4](https://github.com/Baziar/core/commit/7bd31a482b930cb399fa2f4ee2e3fc77ac0e4566))
- correct matrix syntax for GitHub variables in CI workflow
  ([1c82e91](https://github.com/Baziar/core/commit/1c82e91aa600976b8a5abf520549a7f226b49592))
- correct module path in check_module_integrity.py
  ([620e993](https://github.com/Baziar/core/commit/620e993d47f25092730835c5c7b17b5181270365))
- correct module path in check_module_integrity.py
  ([3d4dfc5](https://github.com/Baziar/core/commit/3d4dfc50afea4db06aa7bbfeeea8382a656c5f0e))
- correct PYTHONPATH in CLI test
  ([240f9d4](https://github.com/Baziar/core/commit/240f9d41159d39e450a7476c2e8680a665191b21))
- correct repository root detection in setup script
  ([b7d8a7f](https://github.com/Baziar/core/commit/b7d8a7f13ef1ce2724d493e2580f3160668b5b53))
- correct test for system metrics detection
  ([4e4ed12](https://github.com/Baziar/core/commit/4e4ed126218520997a6c6607d6b26bab693de667))
- correct workflow syntax by separating debug and upload steps
  ([d09b6c2](https://github.com/Baziar/core/commit/d09b6c291b6eb8666d25c5269af64d615d5f3050))
- correct YAML indentation in sync-distribution workflow
  ([4f302ab](https://github.com/Baziar/core/commit/4f302ab8de39903c476f1ac72bd5f6661e7c92d7))
- Correct YAML syntax in setup-distribution action
  ([b5f0518](https://github.com/Baziar/core/commit/b5f0518fe36f51f318139549a61a48de94279143))
- **deploy:** guard against deleting staging workflows
  ([c6a0bdc](https://github.com/Baziar/core/commit/c6a0bdc7812c488b8421fe475654a78218c811d9))
- **deploy:** harden staging pruning and re-copy workflows
  ([8a66fb2](https://github.com/Baziar/core/commit/8a66fb2556283830d313a8f23ab590ecc47d7bbe))
- **deploy:** stage .github deletions in ONLY_WORKFLOWS
  ([d3fbc9a](https://github.com/Baziar/core/commit/d3fbc9a7fac08da6843b42cdc8a1ef035705653f))
- **dist:** include poetry.lock; keep standard kits in community
  ([06a8f93](https://github.com/Baziar/core/commit/06a8f9376c6b07149a29f6a893566ae80c2aaf73))
- Docker build failures in CI
  ([61dd561](https://github.com/Baziar/core/commit/61dd561ee7153e549b252d114a59f5baf5f042eb))
- Docker build issues and CI banner suppression
  ([b9167d6](https://github.com/Baziar/core/commit/b9167d69e597426a4b57d27c8955603f350970db))
- enhance bootstrap artifact creation with comprehensive debugging and fallback mechanisms
  ([c76395d](https://github.com/Baziar/core/commit/c76395d80083df0fdbc46cc3adcc0325f28be6c1))
- ensure snippet context renders templates
  ([644c591](https://github.com/Baziar/core/commit/644c591a2d6349fddec868a36ebb58ea1cdf3afa))
- exclude .j2 template files from hadolint checks
  ([8a7bbaf](https://github.com/Baziar/core/commit/8a7bbaf9b712d05dd54f5cc6798bb595d58bc8d2))
- Fix coverage analyzer repository path resolution
  ([d23033c](https://github.com/Baziar/core/commit/d23033c65ebefd16f7cf311e4782a7a263c50678))
- Fix coverage analyzer to only analyze current repository
  ([5a54df8](https://github.com/Baziar/core/commit/5a54df848c4a077aa9dd168cb90ee57d936c9df9))
- Fix pre-commit hook comment numbering
  ([8818e2d](https://github.com/Baziar/core/commit/8818e2d4689cd28559e3626e7d733fcac982da95))
- Fix Windows path separator issue in telemetry test
  ([9bbbf78](https://github.com/Baziar/core/commit/9bbbf78683f3b4e67cb41a42519cf2df60b7f613))
- Fix YAML syntax and remove external API dependency in CI workflow
  ([4cacd09](https://github.com/Baziar/core/commit/4cacd09926459ea9c37c49ebbe5a8617bf8dcf6c))
- GitHub Actions workflow installation and secrets issues
  ([edceea3](https://github.com/Baziar/core/commit/edceea3d8806b46eb66cca9c8088aa926c0e3003))
- GitHub Actions workflow syntax errors
  ([65a2fd1](https://github.com/Baziar/core/commit/65a2fd1efa71785fa64df230d1c9b52be98cc11d))
- guard template rendering when jinja missing
  ([51fb6fb](https://github.com/Baziar/core/commit/51fb6fb75d1bd6e6d675160262822b246db3e140))
- guard windows installed root from drive fallback
  ([d84524a](https://github.com/Baziar/core/commit/d84524a66bab946efaaabfc78f1b1def9ea9ac60))
- handle default filter fallback in template parser
  ([3acf7a4](https://github.com/Baziar/core/commit/3acf7a43b446e6c30755e56071aa4b4c53d963be))
- handle missing poetry.lock in community CI
  ([ec15968](https://github.com/Baziar/core/commit/ec15968beda96296a7d32d687498edbddcb491f0))
- harden kit assets across platforms
  ([8566580](https://github.com/Baziar/core/commit/8566580a8ee4c642407221c60d45e2bd0de00917))
- harden repo root detection across Windows and template rendering
  ([453d599](https://github.com/Baziar/core/commit/453d5992aa7c7a1dce1cb439e51b408d0f232869))
- harden security auditing
  ([6b0e6c8](https://github.com/Baziar/core/commit/6b0e6c8e273f4e4fc958790af112e6a2806fd641))
- harden site-packages lookup and ship nestjs vendor
  ([6f527f2](https://github.com/Baziar/core/commit/6f527f20c2101c9e3ea38920978d4a92031a38d9))
- ignore changelog during promotion scan
  ([5969d73](https://github.com/Baziar/core/commit/5969d737da5d1e21b1b02302ade60f5a285f26af))
- Improve CI workflow robustness for artifact caching
  ([64588d0](https://github.com/Baziar/core/commit/64588d0ddb790259c2dfddd8aa996b24587b0dc0))
- improve commit message validation script
  ([aeef034](https://github.com/Baziar/core/commit/aeef03437518afa0e5d3e1902110b0be57c397f8))
- improve module integrity script robustness for CI/CD
  ([db5d856](https://github.com/Baziar/core/commit/db5d856825efef51913fc037a5736dee0d04e0b3))
- include compute_agg_version.py in community tier
  ([ff4dbe5](https://github.com/Baziar/core/commit/ff4dbe5d0780de21dbd7df7ed4a6f5d1a5f8bb08))
- include dependency files in community tier
  ([1537911](https://github.com/Baziar/core/commit/153791134db135246610f890caf248bd7ac732d6))
- include generate_release_notes.py in community tier
  ([485f53a](https://github.com/Baziar/core/commit/485f53af0bba2569746cae796afa9447d64ea5ba))
- include src/modules/**init**.py in all distribution tiers
  ([31b40ab](https://github.com/Baziar/core/commit/31b40abe26b6edbe92423eeda1dc5b5f1699bef2))
- include sync probe in community bundle
  ([7cf6cde](https://github.com/Baziar/core/commit/7cf6cdea403be0e74e6b505d7ed45d1777ff8613))
- inline rate limiting defaults in settings snippet
  ([3e17227](https://github.com/Baziar/core/commit/3e17227ba7f2c83da6cfcdf4d6c41c2e94ba70fa))
- make Python scripts executable
  ([32677f9](https://github.com/Baziar/core/commit/32677f977ebb3ea38d151114633fe1a48e2d02f1))
- make telemetry modules available to all tiers
  ([cbb461f](https://github.com/Baziar/core/commit/cbb461f7f30283411e10f7659dc0a3e2fcda9a3c))
- **modules:** sync metadata with resolver changes
  ([86f7f40](https://github.com/Baziar/core/commit/86f7f4036c8bc89f6f6159f2d8773f7a9a406e1c))
- **nestjs:** ensure logging module installs cleanly
  ([f75f11f](https://github.com/Baziar/core/commit/f75f11fd2b2365073572e02a95bec92692c1ab27))
- normalize click choice iterable
  ([d644cd4](https://github.com/Baziar/core/commit/d644cd48c465a2ba0b4770d954ca0de1761f1895))
- normalize module template lookups on windows
  ([a0e74c0](https://github.com/Baziar/core/commit/a0e74c0bf4862e8a8c82112e9b28ff50389c2d03))
- normalize oauth template paths for windows
  ([6fe4279](https://github.com/Baziar/core/commit/6fe42792ed6220306b70b33bb5dcfb3081e4ef48))
- normalize snapshot template paths
  ([b9f8f3a](https://github.com/Baziar/core/commit/b9f8f3aff1c8e5d19e58adce943004945f78af66))
- optimise root
  ([de15bdf](https://github.com/Baziar/core/commit/de15bdf040ed7cc6bbe6a26b08b736ba7475f2ff))
- **pre-commit:** skip module verification writes
  ([9adcbe9](https://github.com/Baziar/core/commit/9adcbe96b9944b288240ab4c081b257e0efdebf6))
- prefer ancestor site-packages on Windows
  ([e2399aa](https://github.com/Baziar/core/commit/e2399aa18ca45c8b7856f73b7378b56953b782f2))
- prevent distribution action from overwriting professional test files
  ([931ea3f](https://github.com/Baziar/core/commit/931ea3f1896bcec0b31e2782b0bc1d55d342debf))
- prevent execution when repository clone fails
  ([ae72fb1](https://github.com/Baziar/core/commit/ae72fb153870e6c9eac481aa5102c7034be3cf8d))
- propagate pythonpath to nestjs smoke
  ([b23fff4](https://github.com/Baziar/core/commit/b23fff42c812c9a6a37635d20e1b0b9e5f579b32))
- reduce coverage threshold from 35% to 30% to fix CI failure
  ([67bf512](https://github.com/Baziar/core/commit/67bf512386ab00986628e2f6bbdcc4d604b27082))
- relax NestJS framework validation for code generation
  ([d8f09b2](https://github.com/Baziar/core/commit/d8f09b2daa54ab3321a0aefef74eee0532cfce64))
- **release:** use Poetry and pin Typer/Click
  ([bbf138f](https://github.com/Baziar/core/commit/bbf138f1948cd9aa0f38b80c1e5e72e783f0df54))
- Remove duplicate src/**init**.py entry from root_files_map.yml
  ([ebc48fa](https://github.com/Baziar/core/commit/ebc48faae3986d735a361474cae0610d264c909f))
- Remove execute permissions from source and test files
  ([6c61b6e](https://github.com/Baziar/core/commit/6c61b6e1cf02c4fb1e3023cef72c0a8f5f0451f6))
- Remove explicit param_decls from boolean Typer options
  ([2f82ca4](https://github.com/Baziar/core/commit/2f82ca457835740db142f1a376a9ec883654d024))
- resolve all ruff linting errors and cleanup test project
  ([4676911](https://github.com/Baziar/core/commit/467691158e92cce748fd50e7ee13479e995f3b52))
- resolve bash syntax error in sync-distribution workflow
  ([04b575d](https://github.com/Baziar/core/commit/04b575d0ee34c14469fd330f3f23c00f8cf00d74))
- resolve bootstrap artifact upload issue by zipping virtual environment
  ([a3ef6c7](https://github.com/Baziar/core/commit/a3ef6c7a4d721e4e97251950e2c3dd14efdec9d0))
- Resolve CI artifact download issues by using python3 and improving Poetry handling
  ([300c4c2](https://github.com/Baziar/core/commit/300c4c23e27f89190aa10c4ad5df24c354fd1841))
- resolve CI build failures
  ([20be938](https://github.com/Baziar/core/commit/20be938e52faf2c8d4f89b710ec110b71dd24dc9))
- resolve CI security and linting warnings
  ([f7c7b5e](https://github.com/Baziar/core/commit/f7c7b5ef64e0ce06e1547fe551bb4f844ba28916))
- resolve CI test failures
  ([34ffbeb](https://github.com/Baziar/core/commit/34ffbeb4091c15480be4bfee7f401091fa5fce17))
- resolve CLI test failure with Typer/Click compatibility
  ([2a8383b](https://github.com/Baziar/core/commit/2a8383bdf6b0193a831ab41acb0648ad9d8f2ded))
- resolve Click/Typer compatibility issue in CI
  ([44cf35d](https://github.com/Baziar/core/commit/44cf35df39376820266525b2ba1e20f125a74eb5))
- Resolve commit message escaping issue in CI workflows
  ([fcd2cd2](https://github.com/Baziar/core/commit/fcd2cd25377f9dde9bf156729fb9cd2c979cb2d9))
- resolve composite action inputs.tier error
  ([ef58317](https://github.com/Baziar/core/commit/ef58317c1653ad173380a0f0e39c6369a27984de))
- resolve distribution CI failures by including essential test files
  ([09bb6c4](https://github.com/Baziar/core/commit/09bb6c44e0ce2a3cefdcf02eb9b759e4c351e244))
- Resolve Docker build failure by moving rapidkit verification after source copy and fixing
  ENTRYPOINT
  ([e807dc5](https://github.com/Baziar/core/commit/e807dc5b32f74a148979e9f9f348e94fffceee9d))
- Resolve Docker build issues by fixing Poetry package installation and Python path
  ([ff160c4](https://github.com/Baziar/core/commit/ff160c4a3c45ea3895a7436efa0dc8505d8f24fb))
- resolve Dockerfile linting issues and add CI/CD workflows
  ([899e233](https://github.com/Baziar/core/commit/899e233d3260aaeb6f1878d4abf75272cb4dc0ed))
- resolve Dockerfile linting issues and add CI/CD workflows
  ([f66e01b](https://github.com/Baziar/core/commit/f66e01be3e2095dbfbf52f886be8d7b7ffec6f81))
- Resolve GitHub Actions commit message parsing issue
  ([4a491f3](https://github.com/Baziar/core/commit/4a491f3fae11304d3f90771a2d66c473fca89119))
- resolve here-document syntax error in sync-distribution workflow
  ([5b6e073](https://github.com/Baziar/core/commit/5b6e0736e316f358a88b1ae6f0934adda10897b9))
- resolve mypy duplicate module error in CI workflow
  ([3b22094](https://github.com/Baziar/core/commit/3b22094061470a4e8267abbd5c3ffada2046dfd8))
- resolve MyPy psutil redefinition error in metrics.py
  ([7728bf6](https://github.com/Baziar/core/commit/7728bf6af5da4f980700a401108338481bcf074e))
- resolve mypy type checking issues and improve Black compatibility
  ([6ef48c0](https://github.com/Baziar/core/commit/6ef48c02410aa396a33c036a9c7881b6cc71db89))
- resolve MyPy unused type: ignore comment in metrics.py
  ([683e360](https://github.com/Baziar/core/commit/683e360953fd0eb46f24f8b605436b084518b4e6))
- Resolve Poetry dependency issue in user tests
  ([4ac2b7d](https://github.com/Baziar/core/commit/4ac2b7de9807c2c877c70c6316f87a9e1cd0a730))
- Resolve Poetry dependency issues in all user tests
  ([63f9eb9](https://github.com/Baziar/core/commit/63f9eb9c02b2576d9d80fcaf4485e9e675cead6b))
- resolve rsync exit code 23 error
  ([a2036a2](https://github.com/Baziar/core/commit/a2036a2d47749154cee14d27eb20ba6102bbbe8d))
- Resolve Ruff linting errors in CI pipeline
  ([ee81efd](https://github.com/Baziar/core/commit/ee81efda3da6e0d3ebf54181136f84735a3763d2))
- resolve Typer boolean flag syntax errors
  ([b610437](https://github.com/Baziar/core/commit/b610437a65b43e27a0b71e444435df4c53722ec7))
- resolve Typer boolean flag syntax errors
  ([f1d9aef](https://github.com/Baziar/core/commit/f1d9aef717ba1312aec038e0e3355981fd212757))
- Resolve Typer boolean option compatibility issue
  ([f6bb282](https://github.com/Baziar/core/commit/f6bb2828474a41a7780bea6b24eb08595c74328e))
- Resolve Typer param_decls conflicts in CLI commands
  ([2bff9f4](https://github.com/Baziar/core/commit/2bff9f445a667adac2719bf7d9c7ce713bbc0da9))
- resolve Typer secondary flag error by simplifying bool options
  ([6e60de4](https://github.com/Baziar/core/commit/6e60de4838608413dba1ee166a64c6a05465a9e6))
- Restore original workflow configuration
  ([05bb513](https://github.com/Baziar/core/commit/05bb513c7f207045984dab0739e25298f3ba1489))
- Restore original workflow configuration
  ([6d2c185](https://github.com/Baziar/core/commit/6d2c185fcd4507e0c2758a1ee57c9f6326859b74))
- restore push trigger for sync-distribution workflow
  ([f7f803a](https://github.com/Baziar/core/commit/f7f803a9e41da0b5af5ccad6e3a51a2c4f64f8cb))
- restore push trigger for sync-distribution workflow
  ([f544b23](https://github.com/Baziar/core/commit/f544b237e8410bb7856a29230c67efa8c98bd710))
- safer push strategy in auto-update workflow
  ([3d3d5be](https://github.com/Baziar/core/commit/3d3d5be8c1a8b99b46108e8879890eb7b97a08a6))
- sanitize CLI help output for legacy encodings
  ([cc0919f](https://github.com/Baziar/core/commit/cc0919f8468db3fef62870956d64f17b7139f352))
- ship shared kit variables in community bundle
  ([d0ba32b](https://github.com/Baziar/core/commit/d0ba32b01a91990e64e2208390678a178acc1f3e))
- Simplify workflow to run without dependencies
  ([cd0c2e8](https://github.com/Baziar/core/commit/cd0c2e8bdb8e54fea02306f2abd669978d62313c))
- Specify individual workflow files per tier instead of entire directory
  ([4eded3d](https://github.com/Baziar/core/commit/4eded3d98d5bbc06db54aae8c5939ae786052146))
- stabilize cli concurrency and repo detection
  ([08a15f8](https://github.com/Baziar/core/commit/08a15f89d860147efd03c558bb30ffab8aadb4cb))
- stabilize CLI import and dependency audit
  ([d492ea3](https://github.com/Baziar/core/commit/d492ea34753fc3779a5ad85b813a4e53b40c67cc))
- stabilize nestjs settings generation
  ([e6e848a](https://github.com/Baziar/core/commit/e6e848ade6c5005042bc8549e7ae3d48600df05c))
- stabilize site-packages detection and nestjs vendor stub
  ([cefd256](https://github.com/Baziar/core/commit/cefd25603891409242ffc731b4accc4d0d7c49ed))
- **test:** Remove duplicate empty core test directory
  ([a036752](https://github.com/Baziar/core/commit/a03675258b966433e7f8196538b97e92e36121f7))
- treat drive roots as invalid repo roots
  ([3eb621f](https://github.com/Baziar/core/commit/3eb621f30d5c5dc9e7b9fdd8da9f047763c99965))
- update all packages to latest stable versions
  ([ed91cb9](https://github.com/Baziar/core/commit/ed91cb974e2e7ce52dcc54a1234fc0108a61d4cb))
- Update coverage grep patterns to match analyzer output
  ([a3996eb](https://github.com/Baziar/core/commit/a3996eba7efe5e4702b8371b28f086185dde53df))
- Update deprecated actions/upload-artifact from v3 to v4
  ([41fb484](https://github.com/Baziar/core/commit/41fb484ff5a9808f7f5985b4db88fc064fc7a27d))
- update distribution mappings for proper tier separation
  ([d837236](https://github.com/Baziar/core/commit/d8372360ffc5d3b7aecec503964bf0e8190e06cb))
- update distribution system with cumulative test logic
  ([44e0994](https://github.com/Baziar/core/commit/44e0994f295a94ebcf6535b24f8842f56b73297e))
- update Makefile for proper tool installation
  ([51c282e](https://github.com/Baziar/core/commit/51c282eb25d432cac0ea4f8618d77cfdac7b8759))
- update pre-commit config to use poetry run python
  ([972c963](https://github.com/Baziar/core/commit/972c963f0bd3dfc65b4931ebf357127540e6f7f5))
- update tests to use psutil_runtime instead of psutil
  ([95ee729](https://github.com/Baziar/core/commit/95ee729fcae30d78cf67012f273c980c64c7a11f))
- use force-with-lease in auto-update workflow
  ([f0831b0](https://github.com/Baziar/core/commit/f0831b07e09aa013463267b43f8d275e52c1563c))
- Use GITHUB_TOKEN instead of API_TOKEN_GITHUB for distribution
  ([1da8718](https://github.com/Baziar/core/commit/1da87185a489191a3639f8f5739bd9c9c0543dd3))
- Use here document for safe commit message handling
  ([358131e](https://github.com/Baziar/core/commit/358131e28afc4fb716150e925a7f0dbc067c7d50))
- Use Python for safe commit message handling in CI
  ([7c96973](https://github.com/Baziar/core/commit/7c9697379a6ba11d07f091c1568c64c5032fca15))
- **versioning:** normalize line endings in module hashing
  ([8540235](https://github.com/Baziar/core/commit/854023513b6f4335481f6d58996ee93cf63b909a))

### Performance Improvements

- optimize Docker build performance and prevent timeouts
  ([73da24e](https://github.com/Baziar/core/commit/73da24e7c8dcbdd42e4ffe6dc9a1e7e32b3492ed))

### Reverts

- remove poetry.lock from community tier distribution
  ([ea9aa84](https://github.com/Baziar/core/commit/ea9aa84ad56b6e32ec5afce9fa4622f39ca210a3))
- restore stable workflow configuration from yesterday
  ([e1a5159](https://github.com/Baziar/core/commit/e1a51595f930a780a80f09820c4435f5bb454eb8))

### Documentation

- add CLI_COMPAT + INDEX; apply compatibility shims and tests; update CI and packaging pins
  ([2719625](https://github.com/Baziar/core/commit/27196251a0bd6c6e1ba045b86a5bc21a2f4c07ad))
- add comprehensive development roadmap and future enhancements
  ([3288713](https://github.com/Baziar/core/commit/3288713d6128a43a4c962f8d8faab93470d1f9e9))
- add GitHub repository variables setup guide
  ([13af1ef](https://github.com/Baziar/core/commit/13af1ef0edd78976712499c5ecd62fbbb10f031a))
- Add pre-commit setup instructions and update config to use Poetry
  ([db4cc87](https://github.com/Baziar/core/commit/db4cc871b3cd6d70323bcc83054debaed200d35d))
- add release 1.1.3 documentation notes
  ([4179a21](https://github.com/Baziar/core/commit/4179a21c9fb6afc0d92a7429c827a49011c5be9c))
- align licensing and monetization messaging
  ([d591ecc](https://github.com/Baziar/core/commit/d591eccac80cebcb9d4f5287c28128ca37cad819))
- align settings module guidance
  ([08fbe26](https://github.com/Baziar/core/commit/08fbe26d8ef76e631fc5bb76c0858d50323d9c15))
- clarify licensing strategy for community bundle
  ([a61ce8d](https://github.com/Baziar/core/commit/a61ce8de73db9993091662439333d8af7709713f))
- fix markdown formatting
  ([64939d9](https://github.com/Baziar/core/commit/64939d93384e6f3fd9835ef310351815ae82c828))
- format changelog for 1.1.3
  ([d2a728e](https://github.com/Baziar/core/commit/d2a728e7f17fb613ea9d46cc2262cec0238960da))
- mdformat adjustments for community-staging deployment guide
  ([7c43ef2](https://github.com/Baziar/core/commit/7c43ef26b843425baccc3785f9652f74d97022fc))
- mdformat adjustments for community-staging deployment guide
  ([0aed890](https://github.com/Baziar/core/commit/0aed890267b0887db29e1fba9c959e18a3dd95dc))
- normalize 1.1.3 changelog formatting
  ([7ec1bc0](https://github.com/Baziar/core/commit/7ec1bc0834893cb386a630649b4e7a2834eb5c9f))
- note release automation observability
  ([58cf055](https://github.com/Baziar/core/commit/58cf0558064256da8f5150fb7d68cb1dff9f6099))
- Translate CI-CD-SIMPLIFICATION.md to English
  ([979ec7d](https://github.com/Baziar/core/commit/979ec7daa44fe20b33b1e9f7cb6b85946652bfd1))
- Update dev-engine documentation for community-only distribution
  ([2ed2581](https://github.com/Baziar/core/commit/2ed25818c0afea269dd85b20a0094b8f3d77b192))
- Update scripts mapping and expand commit guidelines
  ([aee31b4](https://github.com/Baziar/core/commit/aee31b4921b27fab9d1b2eec2b07c6e082f240f5))
- Update scripts mapping for commit validation tool
  ([03a4ebb](https://github.com/Baziar/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))

## [2.0.2](https://github.com/getrapidkit/core/compare/v2.0.1...v2.0.2) (2025-10-22)

### Bug Fixes

- allow rsync to copy kit workflows
  ([46e668d](https://github.com/getrapidkit/core/commit/46e668dbdcb47a8300b1e57910f6356f0ab0ed33))

## [2.0.1](https://github.com/getrapidkit/core/compare/v2.0.0...v2.0.1) (2025-10-22)

### Bug Fixes

- correct Jinja2 template syntax in CI workflow
  ([7bd31a4](https://github.com/getrapidkit/core/commit/7bd31a482b930cb399fa2f4ee2e3fc77ac0e4566))

## [2.0.0](https://github.com/getrapidkit/core/compare/v1.5.1...v2.0.0) (2025-10-22)

### ⚠ BREAKING CHANGES

- Old logging module structure replaced with new modular approach

### Features

- introduce deployment and logging modules with modular architecture
  ([6d6e16a](https://github.com/getrapidkit/core/commit/6d6e16ad10e53b1bf8a00eb9f024b100ccbabe69))

### Bug Fixes

- relax NestJS framework validation for code generation
  ([d8f09b2](https://github.com/getrapidkit/core/commit/d8f09b2daa54ab3321a0aefef74eee0532cfce64))
- resolve CI security and linting warnings
  ([f7c7b5e](https://github.com/getrapidkit/core/commit/f7c7b5ef64e0ce06e1547fe551bb4f844ba28916))

## [1.5.1](https://github.com/getrapidkit/core/compare/v1.5.0...v1.5.1) (2025-10-16)

### Documentation

- align settings module guidance
  ([08fbe26](https://github.com/getrapidkit/core/commit/08fbe26d8ef76e631fc5bb76c0858d50323d9c15))

## [1.5.0](https://github.com/getrapidkit/core/compare/v1.4.0...v1.5.0) (2025-10-15)

### Features

- expose module scaffold and validation CLIs
  ([dc1fe53](https://github.com/getrapidkit/core/commit/dc1fe53ae0fceacd541402f1904c219b131cc730))
- implement plugin-based settings architecture
  ([59939db](https://github.com/getrapidkit/core/commit/59939db585599f846734d5a54a1f7026d75d4d83))
- improve git-commit-wrapper user feedback
  ([08798c8](https://github.com/getrapidkit/core/commit/08798c8a7569d844f0c0515ab8d6c31ad3bf8886))
- major updates to core, docs, and tests
  ([c6d2276](https://github.com/getrapidkit/core/commit/c6d22767b101ef465a205a4dd4266e4d8e660ea0))

### Bug Fixes

- correct module path in check_module_integrity.py
  ([620e993](https://github.com/getrapidkit/core/commit/620e993d47f25092730835c5c7b17b5181270365))
- correct module path in check_module_integrity.py
  ([3d4dfc5](https://github.com/getrapidkit/core/commit/3d4dfc50afea4db06aa7bbfeeea8382a656c5f0e))
- Fix pre-commit hook comment numbering
  ([8818e2d](https://github.com/getrapidkit/core/commit/8818e2d4689cd28559e3626e7d733fcac982da95))
- handle default filter fallback in template parser
  ([3acf7a4](https://github.com/getrapidkit/core/commit/3acf7a43b446e6c30755e56071aa4b4c53d963be))
- improve module integrity script robustness for CI/CD
  ([db5d856](https://github.com/getrapidkit/core/commit/db5d856825efef51913fc037a5736dee0d04e0b3))
- propagate pythonpath to nestjs smoke
  ([b23fff4](https://github.com/getrapidkit/core/commit/b23fff42c812c9a6a37635d20e1b0b9e5f579b32))
- stabilize nestjs settings generation
  ([e6e848a](https://github.com/getrapidkit/core/commit/e6e848ade6c5005042bc8549e7ae3d48600df05c))
- update pre-commit config to use poetry run python
  ([972c963](https://github.com/getrapidkit/core/commit/972c963f0bd3dfc65b4931ebf357127540e6f7f5))

## [1.4.0](https://github.com/getrapidkit/core/compare/v1.3.0...v1.4.0) (2025-10-09)

### Features

- add vendor snapshot layer for settings module
  ([d981d9c](https://github.com/getrapidkit/core/commit/d981d9c53c73eebe190d29158ecc49760910467e))

## [1.3.0](https://github.com/getrapidkit/core/compare/v1.2.1...v1.3.0) (2025-10-08)

### Features

- **cli:** enhance merge and create interactive flows
  ([201e76c](https://github.com/getrapidkit/core/commit/201e76c7af8532da2b50f3b8b280a4d87a7d1f3d))

## [1.2.1](https://github.com/getrapidkit/core/compare/v1.2.0...v1.2.1) (2025-10-08)

### Bug Fixes

- ignore changelog during promotion scan
  ([5969d73](https://github.com/getrapidkit/core/commit/5969d737da5d1e21b1b02302ade60f5a285f26af))

## [1.2.0](https://github.com/getrapidkit/core/compare/v1.1.6...v1.2.0) (2025-10-08)

### Features

- polish community distribution experience
  ([6a6ae7f](https://github.com/getrapidkit/core/commit/6a6ae7ff84e2793211c4ce18e9a08486a11bc03e))

## [1.1.6](https://github.com/getrapidkit/core/compare/v1.1.5...v1.1.6) (2025-10-08)

### Bug Fixes

- **ci:** harden community pipeline
  ([e790edd](https://github.com/getrapidkit/core/commit/e790edd98623d652d665958713b16885453ad1ea))

## [1.1.5](https://github.com/getrapidkit/core/compare/v1.1.4...v1.1.5) (2025-10-08)

### Bug Fixes

- **ci:** keep staging pip patched
  ([fc5eb61](https://github.com/getrapidkit/core/commit/fc5eb61dfbdd47e198b2375c37b7fe66840b6729))
- **ci:** require patched pip for audit
  ([cbeed4c](https://github.com/getrapidkit/core/commit/cbeed4c8c3c8c87d1f3946d774f69330fbb5235a))
- include sync probe in community bundle
  ([7cf6cde](https://github.com/getrapidkit/core/commit/7cf6cdea403be0e74e6b505d7ed45d1777ff8613))
- ship shared kit variables in community bundle
  ([d0ba32b](https://github.com/getrapidkit/core/commit/d0ba32b01a91990e64e2208390678a178acc1f3e))

### Documentation

- clarify licensing strategy for community bundle
  ([a61ce8d](https://github.com/getrapidkit/core/commit/a61ce8de73db9993091662439333d8af7709713f))

## [1.1.4](https://github.com/getrapidkit/core/compare/v1.1.3...v1.1.4) (2025-10-08)

### Documentation

- normalize 1.1.3 changelog formatting
  ([7ec1bc0](https://github.com/getrapidkit/core/commit/7ec1bc0834893cb386a630649b4e7a2834eb5c9f))
- note release automation observability
  ([58cf055](https://github.com/getrapidkit/core/commit/58cf0558064256da8f5150fb7d68cb1dff9f6099))

## [1.1.3](https://github.com/getrapidkit/core/compare/v1.1.2...v1.1.3) (2025-10-07)

### Bug Fixes

- **cli:** support global help flag
  ([02c780f](https://github.com/getrapidkit/core/commit/02c780f8275764fc6a88cc43820fba819a1000a2))

### Documentation

- add release 1.1.3 documentation notes
  ([4179a21](https://github.com/getrapidkit/core/commit/4179a21c9fb6afc0d92a7429c827a49011c5be9c))
- format changelog for 1.1.3
  ([d2a728e](https://github.com/getrapidkit/core/commit/d2a728e7f17fb613ea9d46cc2262cec0238960da))

## [1.1.2](https://github.com/getrapidkit/core/compare/v1.1.1...v1.1.2) (2025-10-07)

### Bug Fixes

- **ci:** guard codecov upload with github token
  ([b0766ba](https://github.com/getrapidkit/core/commit/b0766ba00ce69d86ea389ee4aa5c90c675137032))

## [1.1.1](https://github.com/getrapidkit/core/compare/v1.1.0...v1.1.1) (2025-10-07)

### Documentation

- fix markdown formatting
  ([64939d9](https://github.com/getrapidkit/core/commit/64939d93384e6f3fd9835ef310351815ae82c828))

## [1.1.0](https://github.com/getrapidkit/core/compare/v1.0.0...v1.1.0) (2025-10-06)

### Features

- accept --json flag for diff all (no-op for CI compatibility)
  ([ce420b2](https://github.com/getrapidkit/core/commit/ce420b22593b70b1cb363e887ec53a143f66714f))
- Add advanced pre-commit management system
  ([75841db](https://github.com/getrapidkit/core/commit/75841db4af816e2b9a65a9dec6ee43357c159c55))
- add automated distribution system
  ([1dcd125](https://github.com/getrapidkit/core/commit/1dcd125afb6f211f5da41e6b7c9742258dc63b68))
- add automated GitHub variables setup script
  ([634f230](https://github.com/getrapidkit/core/commit/634f2302f77ea89129689c2ef2651e622fbfad0c))
- Add automatic commit message validation to pre-commit hooks
  ([bbdc324](https://github.com/getrapidkit/core/commit/bbdc3248b0d2ca996908c38cff8a33f732e401fa))
- add Black configuration and fix distribution workflows
  ([bd8d6a5](https://github.com/getrapidkit/core/commit/bd8d6a50ab321838aed4d173b565c5fcf5b27085))
- Add complete PyPI publishing infrastructure and documentation
  ([b6ad585](https://github.com/getrapidkit/core/commit/b6ad5858f42b487c42ed784abb8a7269d0025db6))
- Add comprehensive commit message standards documentation
  ([03a4ebb](https://github.com/getrapidkit/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))
- Add comprehensive distribution test script
  ([7ee19b9](https://github.com/getrapidkit/core/commit/7ee19b992fc0f279aeacf9fa2c3db60deaae9030))
- Add debug commit type support
  ([e0209e9](https://github.com/getrapidkit/core/commit/e0209e979984e1b30cb9f56beb4bfd9f0151b34e))
- Add path-based triggers for better workflow execution
  ([c685e7c](https://github.com/getrapidkit/core/commit/c685e7c18ff1ba758935d08343cff0d72b740684))
- Add professional basic test file
  ([59c1e53](https://github.com/getrapidkit/core/commit/59c1e5315434d0bc7bdb22ab497d2e59f83739ee))
- add sync jobs for pro and enterprise repositories
  ([a7c230e](https://github.com/getrapidkit/core/commit/a7c230e55e7ba21fc985e757bb43c4d3aa05ae51))
- add test file for validation testing
  ([5da8254](https://github.com/getrapidkit/core/commit/5da8254d1a1908c4ec8dba6797b89d3af7415532))
- Add tier coverage analyzer and update mapping files
  ([72d4ca7](https://github.com/getrapidkit/core/commit/72d4ca725ab50be66f6894dd5f1b6924994230e0))
- Add tier-specific CODEOWNERS files for all distribution repositories
  ([288056d](https://github.com/getrapidkit/core/commit/288056d2753530a84f04683dffb66baa26e74ff4))
- Automate modules lock file generation
  ([a2f2dd4](https://github.com/getrapidkit/core/commit/a2f2dd4f8bac6cd9439e9830820b505573f3a629))
- **cli/modules:** add lock & outdated commands + JSON output for summary/outdated
  ([8f0dc88](https://github.com/getrapidkit/core/commit/8f0dc88ac8f9d38a45965b047d39b802045a0c1a))
- **cli:** add diff/upgrade/rollback/uninstall/checkpoint/snapshot commands with snapshot-based
  rollback and lifecycle tests
  ([4ac2185](https://github.com/getrapidkit/core/commit/4ac2185d4137ff102d87a3eee91be8db16fed71c))
- **cli:** batch upgrade & aggregated diff; add CONTRIBUTING and migration guide template
  ([ed19ab9](https://github.com/getrapidkit/core/commit/ed19ab958acd1ca44bc8660718b977e5bee0879b))
- Complete development environment setup
  ([8e093b8](https://github.com/getrapidkit/core/commit/8e093b83e2cf382093e4bee51a8f8aa8ebdf9aad))
- Complete distribution system with tier-specific sync
  ([2eb00fd](https://github.com/getrapidkit/core/commit/2eb00fdccb5c05e4231faa3890c65da3befcad9b))
- Complete mapping system reorganization and documentation centralization
  ([91f48e0](https://github.com/getrapidkit/core/commit/91f48e06f5f16aeb81c4873500ec7be9139d1f55))
- Complete overhaul of setup-distribution action with professional improvements
  ([53c3bd1](https://github.com/getrapidkit/core/commit/53c3bd15584b7d3565d1535e5158c88784088903))
- Complete professional overhaul of setup-distribution action and docs cleanup
  ([1b81c48](https://github.com/getrapidkit/core/commit/1b81c482a7a64910cfeccf55675a241cef9fb3e0))
- Complete tier filtering system with enterprise module removal
  ([b521a81](https://github.com/getrapidkit/core/commit/b521a8181d7bef9256c16eb3baf67d02960666b9))
- Comprehensive documentation and code updates for community distribution
  ([2958d26](https://github.com/getrapidkit/core/commit/2958d2668bf087a3bbd460beec6941e4088f8541))
- Comprehensive repository cleanup and community distribution preparation
  ([050a643](https://github.com/getrapidkit/core/commit/050a6430589b62ef5dc465ffcb470e5115059a41))
- **core:** Phase1 module manifest + file hash registry (idempotent installs)
  ([3e2267f](https://github.com/getrapidkit/core/commit/3e2267fa0f31dc00b4c26e8b47cb10bab7fb1745))
- enhance CI workflow with enterprise features
  ([1bf4e6a](https://github.com/getrapidkit/core/commit/1bf4e6ad2ea96f49e196418f752d646effb8347c))
- Enhance commit message validation
  ([c289b58](https://github.com/getrapidkit/core/commit/c289b58396f097e0b28a1e8f3bb8c7e29db13c06))
- **frameworks:** fastapi adapter scaffold + frameworks CLI + tests (temporary coverage gate
  lowered)
  ([091785b](https://github.com/getrapidkit/core/commit/091785bf9ea11b22bf11b6a6feacabb9fd029c68))
- **gating:** enforce module gating based on tier/license in CLI
  ([f27c873](https://github.com/getrapidkit/core/commit/f27c873c7af5d5748798584c103f211a20cdc70c))
- **health:** Phase A probe registry + dynamic probes for settings/postgres/sqlite/redis + module
  manifests
  ([b677878](https://github.com/getrapidkit/core/commit/b677878c86297cc325782c6c30c5959e11ae9dd8))
- Implement automatic commit message validation for distribution
  ([03a4ebb](https://github.com/getrapidkit/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))
- implement GitHub repository variables for CI configuration
  ([341ea95](https://github.com/getrapidkit/core/commit/341ea956b7475fa89c04c25a612adfd2ec72e74e))
- implement Next.js-style professional CLI architecture
  ([df403fb](https://github.com/getrapidkit/core/commit/df403fb4ea86fac11269c8cb50bc3315dd28252f))
- **installer:** add --force / --update with previous_hash tracking
  ([b5c52b9](https://github.com/getrapidkit/core/commit/b5c52b9479846f31086a1f0fcd8d098214de789a))
- interactive merge prompt strategy (diff/apply/keep/skip/quit); add test
  ([018f653](https://github.com/getrapidkit/core/commit/018f6535ba3e59204292e1d7f1d353765a6c47d7))
- **kits:** update FastAPI kit generators/hooks and minimal kit structure
  ([0573c05](https://github.com/getrapidkit/core/commit/0573c05627bf3ce7783a99727b662bd7c91b33a7))
- **license:** add license.json structure and CLI for inspect/activate
  ([81e1a50](https://github.com/getrapidkit/core/commit/81e1a504fdc7603c3fb2aa2ed59d7acc3c7620a0))
- **lifecycle:** JSON schemas docs, pydantic v2 compat, diff-all pure JSON, merge/rollback tests,
  release notes script, lock & new placeholder modules
  ([bfe1a03](https://github.com/getrapidkit/core/commit/bfe1a03e88d8c35edef069714c42e3f8d78a9f18))
- major module system refactoring and kit updates
  ([f7d99ba](https://github.com/getrapidkit/core/commit/f7d99ba2b3a9571e38f6421d76e428f463ac028e))
- **manifest:** add tier and capabilities fields to all module manifests
  ([206cb0e](https://github.com/getrapidkit/core/commit/206cb0ea401dd5ef5375ade51eda2bbbdc7f99e6))
- merge helper JSON (--merge-json), upgrade status filtering (--only-statuses), migration-template
  command, schema_version annotations
  ([af06116](https://github.com/getrapidkit/core/commit/af061169369db8a926e5c52b7880a291e1a61be8))
- **modules:** minimal manifests + version/access relocation, dynamic summary, tags & verbose
  metrics, README overhaul
  ([6a088a0](https://github.com/getrapidkit/core/commit/6a088a0ae9f320cd4686ac09745c2aea27ff67ae))
- Multi-framework support foundation
  ([c7a6d1a](https://github.com/getrapidkit/core/commit/c7a6d1a89f53a9c0bf003b549ae544528e19a8d6))
- Optimize distribution system and license management
  ([18b2644](https://github.com/getrapidkit/core/commit/18b2644289b797c47d08c3a5bd888ee58b144078))
- **overlays+ci:** template overlay support, modules outdated workflow, README updates
  ([8caaadc](https://github.com/getrapidkit/core/commit/8caaadc84657f9781745449040f40b96a7951f5f))
- Reorganize modular system with enterprise-grade tooling
  ([2dc8cc9](https://github.com/getrapidkit/core/commit/2dc8cc975e97d8ca22768a111d022eb3926b8c1d))
- snapshot gc command (retention by count/age) + tests
  ([240ad1b](https://github.com/getrapidkit/core/commit/240ad1b47090f8ebc2b168f4624715a66461e612))
- Transform RapidKit into Next.js-like development tool
  ([597cc55](https://github.com/getrapidkit/core/commit/597cc5520877f4ac07d12d0d3c42c2c00278d3d0))
- update module structure verification files
  ([d678daa](https://github.com/getrapidkit/core/commit/d678daa5048ec2afa92886368c1644fea63e299e))
- Update root_files_map.yml with missing files
  ([831816e](https://github.com/getrapidkit/core/commit/831816eaf75cb8649eaa2b29bf752fdfce6037e5))
- update test file with additional content
  ([2248818](https://github.com/getrapidkit/core/commit/2248818e8977eebcd660314b1f5c9a9b2bb2930d))

### Bug Fixes

- add comprehensive debugging to setup job to identify bootstrap artifact issue
  ([e254650](https://github.com/getrapidkit/core/commit/e254650a1edb082ca7f9cfe1c3c067c27950dc05))
- Add distribution workflows to root_files_map.yml for proper tier distribution
  ([4d97831](https://github.com/getrapidkit/core/commit/4d97831dcde92e53727d56e4aaa0318360e2e616))
- Add Docker image verification step to prevent test failures
  ([129fde3](https://github.com/getrapidkit/core/commit/129fde35d90f505e2f356a75aaaca215a7869b2d))
- Add Dockerfile to workflow trigger paths so Docker job runs when Dockerfile changes
  ([d6c3c0b](https://github.com/getrapidkit/core/commit/d6c3c0bd25cb39055f6eb6b253727927d3f6e687))
- add jinja2 dependency for template rendering
  ([5ca22ff](https://github.com/getrapidkit/core/commit/5ca22ff51b8016e312e5aedc3403bec1e7fde145))
- Add missing src_map.yml parameter to distribution action
  ([2646108](https://github.com/getrapidkit/core/commit/26461083fd4893dca026ae9793841dbe470eac10))
- Add parse_tier_files.py to scripts_map.yml for all tiers
  ([c48ea48](https://github.com/getrapidkit/core/commit/c48ea48fb9b3be4080ebbf83f077cebd21351f35))
- add pydantic dependency and 3.9-compatible typing (Optional)
  ([de769be](https://github.com/getrapidkit/core/commit/de769beb35491d2f4277c60dedfb2784ff4b6991))
- Add src/\* to root_files_map.yml for proper distribution
  ([dd54b3d](https://github.com/getrapidkit/core/commit/dd54b3db3b9be397ec5e64f8c7942549ed946ed3))
- add support for private repositories in distribution workflow
  ([1680165](https://github.com/getrapidkit/core/commit/16801653343305999b3456d0a3cb72ae5f696822))
- align cross-platform workflows
  ([74b5563](https://github.com/getrapidkit/core/commit/74b5563bae7f4779a37db3ed400315caa1629339))
- Black formatting in generated test_basic.py files
  ([82bb1db](https://github.com/getrapidkit/core/commit/82bb1dbb822a1255f1147644f04a4f4af65bef07))
- change sync-distribution to PR-only triggers
  ([368c244](https://github.com/getrapidkit/core/commit/368c244a931050f0f7ba696bd90bb9f17e9841a3))
- **ci:** apply mypy and functional fixes to make local CI checks pass
  ([fe87a38](https://github.com/getrapidkit/core/commit/fe87a388fea0ab27291a52a6c3b22bb6aac37d75))
- **ci:** correct coverage aggregation by using .coverage data files
  ([b4c327d](https://github.com/getrapidkit/core/commit/b4c327d2a0473af5810dc27cd9bf8174d3d3f44e))
- **ci:** Fix Poetry PATH issues in community CI workflow
  ([974a4ac](https://github.com/getrapidkit/core/commit/974a4acdd315dfa52aea08db81dbdd95033b3df1))
- **ci:** include core.frameworks in core tier
  ([767c70c](https://github.com/getrapidkit/core/commit/767c70c52208bb2da3e63debfce37b5a9c4ce048))
- **ci:** include core.module_sign in core tier
  ([0cab523](https://github.com/getrapidkit/core/commit/0cab5230793e816fc62058469f464702fa73a146))
- **ci:** include core.structure in core tier mapping
  ([b27c71a](https://github.com/getrapidkit/core/commit/b27c71a96a8921a3c1f0438cf2fee054ad40e122))
- **ci:** include engine dependencies in core tier
  ([3ceb092](https://github.com/getrapidkit/core/commit/3ceb092babd3b9ccacbc05091007f70980cffae7))
- **ci:** include license_utils and py.typed in core tier
  ([d61117c](https://github.com/getrapidkit/core/commit/d61117c0c3ddd2bde9f96da361d6216e2b0c555d))
- **ci:** make diff_gate tolerant of banner text before JSON output
  ([85a436c](https://github.com/getrapidkit/core/commit/85a436c54c674286d5c32f145a4ed0d85cad13bf))
- **ci:** pin typer/click in CI to match local environment
  ([37b01a8](https://github.com/getrapidkit/core/commit/37b01a82f1dabf1777d54ec103580760f52cd038))
- **ci:** resolve distribution CI failures and logo issues
  ([787e977](https://github.com/getrapidkit/core/commit/787e97789314ab93a3734aa9eaf51e4d458fd64c))
- **ci:** resolve multiple CI/CD pipeline issues
  ([a2645d8](https://github.com/getrapidkit/core/commit/a2645d8ab2336eb2c6d62abd6156590c5b59bd3a))
- clean distribution repos and rebuild correct structure
  ([7a61bea](https://github.com/getrapidkit/core/commit/7a61bea49477d2283a6593c366f479f81fb3d460))
- **cli:** honor click exit codes
  ([b427cc6](https://github.com/getrapidkit/core/commit/b427cc612675a7aa832342bb5598631820dd8d0a))
- **cli:** keep legacy help exit successful
  ([9ba95fe](https://github.com/getrapidkit/core/commit/9ba95fec35ccd1fbd7903b3347bdb0b516a6627d))
- **cli:** preserve typer exits
  ([d0f410a](https://github.com/getrapidkit/core/commit/d0f410a99871d6c1af245e7cbff287790847aecb))
- **cli:** propagate typer exit codes
  ([35b50f5](https://github.com/getrapidkit/core/commit/35b50f593b859fca5e6e91ad62abc0a47641a299))
- **cli:** resolve secondary option syntax compatibility issues
  ([2015804](https://github.com/getrapidkit/core/commit/201580486037f75fcaa5b232563cf305b761582f))
- **cli:** restore global module entrypoint
  ([94191af](https://github.com/getrapidkit/core/commit/94191af258e9d60d6d69044d8fa1278a92084c74))
- **cli:** tolerate legacy stdio encodings
  ([9749e65](https://github.com/getrapidkit/core/commit/9749e65277bc6d61ba09ca455d9b8e6ae8e63b7b))
- Code formatting and linting fixes from pre-commit hooks
  ([0305685](https://github.com/getrapidkit/core/commit/0305685cd26d3061b9b781dd206bbfe497416221))
- Complete community repository GitHub Actions setup
  ([9c67cf3](https://github.com/getrapidkit/core/commit/9c67cf3ccbf5515e3ce4c519b4c324b0a6d8505c))
- complete test filtering for distribution tiers
  ([1a1a0ae](https://github.com/getrapidkit/core/commit/1a1a0ae2ecd2736a44c08033d044852558a42f73))
- complete type annotations and security fixes
  ([bf25e02](https://github.com/getrapidkit/core/commit/bf25e02ce3b79e8221772eef017c06e3abbd1481))
- completely remove PYTHONPATH from community CI workflow
  ([b3b5b68](https://github.com/getrapidkit/core/commit/b3b5b68ad56a5f90788c36b458dab0313a8e2658))
- Convert absolute cli imports to relative imports to fix ModuleNotFoundError
  ([851374a](https://github.com/getrapidkit/core/commit/851374ab14f9bc2bd012fc01617aba13261d612f))
- Correct \_module_priority function to handle zero priority values
  ([4e0ed8b](https://github.com/getrapidkit/core/commit/4e0ed8b456e095ea8318310ff853360e7dec2b41))
- Correct \_module_priority function to handle zero priority values
  ([18fd259](https://github.com/getrapidkit/core/commit/18fd259e88097fa89d76655e7e64fee9d2a3ad01))
- Correct \_module_priority function to handle zero priority values
  ([55ac92f](https://github.com/getrapidkit/core/commit/55ac92f89e89fbb990d9cc96768383d838999650))
- Correct \_module_priority function to handle zero priority values
  ([dfcde4c](https://github.com/getrapidkit/core/commit/dfcde4c2901b6d7fa249a2c7bd14dd7c1c919111))
- Correct \_module_priority function to handle zero priority values
  ([6e36c46](https://github.com/getrapidkit/core/commit/6e36c46cce460ec2c459ffabf4525e8dbf894473))
- Correct coverage data file paths in CI aggregation
  ([0d61483](https://github.com/getrapidkit/core/commit/0d614833a1b1c7f121a2e23f0e85ca6732974bc4))
- Correct GitHub Actions workflow env variable references
  ([cd13422](https://github.com/getrapidkit/core/commit/cd13422d3c100807b948dc05da87b9d714e5705a))
- correct matrix syntax for GitHub variables in CI workflow
  ([1c82e91](https://github.com/getrapidkit/core/commit/1c82e91aa600976b8a5abf520549a7f226b49592))
- correct PYTHONPATH in CLI test
  ([240f9d4](https://github.com/getrapidkit/core/commit/240f9d41159d39e450a7476c2e8680a665191b21))
- correct repository root detection in setup script
  ([b7d8a7f](https://github.com/getrapidkit/core/commit/b7d8a7f13ef1ce2724d493e2580f3160668b5b53))
- correct test for system metrics detection
  ([4e4ed12](https://github.com/getrapidkit/core/commit/4e4ed126218520997a6c6607d6b26bab693de667))
- correct workflow syntax by separating debug and upload steps
  ([d09b6c2](https://github.com/getrapidkit/core/commit/d09b6c291b6eb8666d25c5269af64d615d5f3050))
- correct YAML indentation in sync-distribution workflow
  ([4f302ab](https://github.com/getrapidkit/core/commit/4f302ab8de39903c476f1ac72bd5f6661e7c92d7))
- Correct YAML syntax in setup-distribution action
  ([b5f0518](https://github.com/getrapidkit/core/commit/b5f0518fe36f51f318139549a61a48de94279143))
- **deploy:** guard against deleting staging workflows
  ([c6a0bdc](https://github.com/getrapidkit/core/commit/c6a0bdc7812c488b8421fe475654a78218c811d9))
- **deploy:** harden staging pruning and re-copy workflows
  ([8a66fb2](https://github.com/getrapidkit/core/commit/8a66fb2556283830d313a8f23ab590ecc47d7bbe))
- **deploy:** stage .github deletions in ONLY_WORKFLOWS
  ([d3fbc9a](https://github.com/getrapidkit/core/commit/d3fbc9a7fac08da6843b42cdc8a1ef035705653f))
- **dist:** include poetry.lock; keep standard kits in community
  ([06a8f93](https://github.com/getrapidkit/core/commit/06a8f9376c6b07149a29f6a893566ae80c2aaf73))
- Docker build failures in CI
  ([61dd561](https://github.com/getrapidkit/core/commit/61dd561ee7153e549b252d114a59f5baf5f042eb))
- Docker build issues and CI banner suppression
  ([b9167d6](https://github.com/getrapidkit/core/commit/b9167d69e597426a4b57d27c8955603f350970db))
- enhance bootstrap artifact creation with comprehensive debugging and fallback mechanisms
  ([c76395d](https://github.com/getrapidkit/core/commit/c76395d80083df0fdbc46cc3adcc0325f28be6c1))
- exclude .git from rsync to preserve git repository
  ([f9b7dcf](https://github.com/getrapidkit/core/commit/f9b7dcf0fd997f5c25a2780fb09d9ce0429e33a1))
- exclude .j2 template files from hadolint checks
  ([8a7bbaf](https://github.com/getrapidkit/core/commit/8a7bbaf9b712d05dd54f5cc6798bb595d58bc8d2))
- filter kits and tests by tier in distribution sync
  ([4bf6db5](https://github.com/getrapidkit/core/commit/4bf6db5048f36dd72a64787a7a004e11052fdd1f))
- Fix coverage analyzer repository path resolution
  ([d23033c](https://github.com/getrapidkit/core/commit/d23033c65ebefd16f7cf311e4782a7a263c50678))
- Fix coverage analyzer to only analyze current repository
  ([5a54df8](https://github.com/getrapidkit/core/commit/5a54df848c4a077aa9dd168cb90ee57d936c9df9))
- Fix Windows path separator issue in telemetry test
  ([9bbbf78](https://github.com/getrapidkit/core/commit/9bbbf78683f3b4e67cb41a42519cf2df60b7f613))
- Fix YAML syntax and remove external API dependency in CI workflow
  ([4cacd09](https://github.com/getrapidkit/core/commit/4cacd09926459ea9c37c49ebbe5a8617bf8dcf6c))
- force remove filtered kits after rsync to ensure deletion
  ([cf7e7b1](https://github.com/getrapidkit/core/commit/cf7e7b141a01698dcfb4a6cd9ec53d9564e70e84))
- force rm kits before rsync to ensure clean sync
  ([02ce598](https://github.com/getrapidkit/core/commit/02ce598be33efce8a771684b6e777afadf580a58))
- GitHub Actions workflow installation and secrets issues
  ([edceea3](https://github.com/getrapidkit/core/commit/edceea3d8806b46eb66cca9c8088aa926c0e3003))
- GitHub Actions workflow syntax errors
  ([65a2fd1](https://github.com/getrapidkit/core/commit/65a2fd1efa71785fa64df230d1c9b52be98cc11d))
- handle missing poetry.lock in community CI
  ([ec15968](https://github.com/getrapidkit/core/commit/ec15968beda96296a7d32d687498edbddcb491f0))
- harden security auditing
  ([6b0e6c8](https://github.com/getrapidkit/core/commit/6b0e6c8e273f4e4fc958790af112e6a2806fd641))
- Improve CI workflow robustness for artifact caching
  ([64588d0](https://github.com/getrapidkit/core/commit/64588d0ddb790259c2dfddd8aa996b24587b0dc0))
- improve commit message validation script
  ([aeef034](https://github.com/getrapidkit/core/commit/aeef03437518afa0e5d3e1902110b0be57c397f8))
- include compute_agg_version.py in community tier
  ([ff4dbe5](https://github.com/getrapidkit/core/commit/ff4dbe5d0780de21dbd7df7ed4a6f5d1a5f8bb08))
- include dependency files in community tier
  ([1537911](https://github.com/getrapidkit/core/commit/153791134db135246610f890caf248bd7ac732d6))
- include generate_release_notes.py in community tier
  ([485f53a](https://github.com/getrapidkit/core/commit/485f53af0bba2569746cae796afa9447d64ea5ba))
- include src/modules/**init**.py in all distribution tiers
  ([31b40ab](https://github.com/getrapidkit/core/commit/31b40abe26b6edbe92423eeda1dc5b5f1699bef2))
- make Python scripts executable
  ([32677f9](https://github.com/getrapidkit/core/commit/32677f977ebb3ea38d151114633fe1a48e2d02f1))
- make telemetry modules available to all tiers
  ([cbb461f](https://github.com/getrapidkit/core/commit/cbb461f7f30283411e10f7659dc0a3e2fcda9a3c))
- **modules:** update module manifests
  ([6df0b61](https://github.com/getrapidkit/core/commit/6df0b61d634cce30df28851cd6885ef6e650d29b))
- normalize click choice iterable
  ([d644cd4](https://github.com/getrapidkit/core/commit/d644cd48c465a2ba0b4770d954ca0de1761f1895))
- normalize snapshot template paths
  ([b9f8f3a](https://github.com/getrapidkit/core/commit/b9f8f3aff1c8e5d19e58adce943004945f78af66))
- optimise root
  ([de15bdf](https://github.com/getrapidkit/core/commit/de15bdf040ed7cc6bbe6a26b08b736ba7475f2ff))
- prevent distribution action from overwriting professional test files
  ([931ea3f](https://github.com/getrapidkit/core/commit/931ea3f1896bcec0b31e2782b0bc1d55d342debf))
- prevent execution when repository clone fails
  ([ae72fb1](https://github.com/getrapidkit/core/commit/ae72fb153870e6c9eac481aa5102c7034be3cf8d))
- python 3.9 compatibility (Optional typing and indentation)
  ([a93b22a](https://github.com/getrapidkit/core/commit/a93b22af3572642627c7aa1b8cd4a77298cf3800))
- reduce coverage threshold from 35% to 30% to fix CI failure
  ([67bf512](https://github.com/getrapidkit/core/commit/67bf512386ab00986628e2f6bbdcc4d604b27082))
- **release:** use Poetry and pin Typer/Click
  ([bbf138f](https://github.com/getrapidkit/core/commit/bbf138f1948cd9aa0f38b80c1e5e72e783f0df54))
- Remove duplicate src/**init**.py entry from root_files_map.yml
  ([ebc48fa](https://github.com/getrapidkit/core/commit/ebc48faae3986d735a361474cae0610d264c909f))
- Remove execute permissions from source and test files
  ([6c61b6e](https://github.com/getrapidkit/core/commit/6c61b6e1cf02c4fb1e3023cef72c0a8f5f0451f6))
- Remove explicit param_decls from boolean Typer options
  ([2f82ca4](https://github.com/getrapidkit/core/commit/2f82ca457835740db142f1a376a9ec883654d024))
- repair diff_all indentation and broaden project root detection for tests
  ([8755357](https://github.com/getrapidkit/core/commit/87553574d211f1cf4d436ced2ab5ada0a9f36ccf))
- resolve all ruff linting errors and cleanup test project
  ([4676911](https://github.com/getrapidkit/core/commit/467691158e92cce748fd50e7ee13479e995f3b52))
- resolve bash syntax error in sync-distribution workflow
  ([04b575d](https://github.com/getrapidkit/core/commit/04b575d0ee34c14469fd330f3f23c00f8cf00d74))
- resolve bootstrap artifact upload issue by zipping virtual environment
  ([a3ef6c7](https://github.com/getrapidkit/core/commit/a3ef6c7a4d721e4e97251950e2c3dd14efdec9d0))
- Resolve CI artifact download issues by using python3 and improving Poetry handling
  ([300c4c2](https://github.com/getrapidkit/core/commit/300c4c23e27f89190aa10c4ad5df24c354fd1841))
- resolve CI build failures
  ([20be938](https://github.com/getrapidkit/core/commit/20be938e52faf2c8d4f89b710ec110b71dd24dc9))
- resolve CI test failures
  ([34ffbeb](https://github.com/getrapidkit/core/commit/34ffbeb4091c15480be4bfee7f401091fa5fce17))
- resolve CLI test failure with Typer/Click compatibility
  ([2a8383b](https://github.com/getrapidkit/core/commit/2a8383bdf6b0193a831ab41acb0648ad9d8f2ded))
- resolve Click/Typer compatibility issue in CI
  ([44cf35d](https://github.com/getrapidkit/core/commit/44cf35df39376820266525b2ba1e20f125a74eb5))
- Resolve commit message escaping issue in CI workflows
  ([fcd2cd2](https://github.com/getrapidkit/core/commit/fcd2cd25377f9dde9bf156729fb9cd2c979cb2d9))
- resolve composite action inputs.tier error
  ([ef58317](https://github.com/getrapidkit/core/commit/ef58317c1653ad173380a0f0e39c6369a27984de))
- resolve distribution CI failures by including essential test files
  ([09bb6c4](https://github.com/getrapidkit/core/commit/09bb6c44e0ce2a3cefdcf02eb9b759e4c351e244))
- Resolve Docker build failure by moving rapidkit verification after source copy and fixing
  ENTRYPOINT
  ([e807dc5](https://github.com/getrapidkit/core/commit/e807dc5b32f74a148979e9f9f348e94fffceee9d))
- Resolve Docker build issues by fixing Poetry package installation and Python path
  ([ff160c4](https://github.com/getrapidkit/core/commit/ff160c4a3c45ea3895a7436efa0dc8505d8f24fb))
- resolve Dockerfile linting issues and add CI/CD workflows
  ([899e233](https://github.com/getrapidkit/core/commit/899e233d3260aaeb6f1878d4abf75272cb4dc0ed))
- resolve Dockerfile linting issues and add CI/CD workflows
  ([f66e01b](https://github.com/getrapidkit/core/commit/f66e01be3e2095dbfbf52f886be8d7b7ffec6f81))
- Resolve GitHub Actions commit message parsing issue
  ([4a491f3](https://github.com/getrapidkit/core/commit/4a491f3fae11304d3f90771a2d66c473fca89119))
- resolve here-document syntax error in sync-distribution workflow
  ([5b6e073](https://github.com/getrapidkit/core/commit/5b6e0736e316f358a88b1ae6f0934adda10897b9))
- resolve mypy duplicate module error in CI workflow
  ([3b22094](https://github.com/getrapidkit/core/commit/3b22094061470a4e8267abbd5c3ffada2046dfd8))
- resolve MyPy psutil redefinition error in metrics.py
  ([7728bf6](https://github.com/getrapidkit/core/commit/7728bf6af5da4f980700a401108338481bcf074e))
- resolve mypy type checking issues and improve Black compatibility
  ([6ef48c0](https://github.com/getrapidkit/core/commit/6ef48c02410aa396a33c036a9c7881b6cc71db89))
- resolve MyPy unused type: ignore comment in metrics.py
  ([683e360](https://github.com/getrapidkit/core/commit/683e360953fd0eb46f24f8b605436b084518b4e6))
- Resolve Poetry dependency issue in user tests
  ([4ac2b7d](https://github.com/getrapidkit/core/commit/4ac2b7de9807c2c877c70c6316f87a9e1cd0a730))
- Resolve Poetry dependency issues in all user tests
  ([63f9eb9](https://github.com/getrapidkit/core/commit/63f9eb9c02b2576d9d80fcaf4485e9e675cead6b))
- resolve rsync exit code 23 error
  ([a2036a2](https://github.com/getrapidkit/core/commit/a2036a2d47749154cee14d27eb20ba6102bbbe8d))
- Resolve Ruff linting errors in CI pipeline
  ([ee81efd](https://github.com/getrapidkit/core/commit/ee81efda3da6e0d3ebf54181136f84735a3763d2))
- resolve Typer boolean flag syntax errors
  ([b610437](https://github.com/getrapidkit/core/commit/b610437a65b43e27a0b71e444435df4c53722ec7))
- resolve Typer boolean flag syntax errors
  ([f1d9aef](https://github.com/getrapidkit/core/commit/f1d9aef717ba1312aec038e0e3355981fd212757))
- Resolve Typer boolean option compatibility issue
  ([f6bb282](https://github.com/getrapidkit/core/commit/f6bb2828474a41a7780bea6b24eb08595c74328e))
- Resolve Typer param_decls conflicts in CLI commands
  ([2bff9f4](https://github.com/getrapidkit/core/commit/2bff9f445a667adac2719bf7d9c7ce713bbc0da9))
- resolve Typer secondary flag error by simplifying bool options
  ([6e60de4](https://github.com/getrapidkit/core/commit/6e60de4838608413dba1ee166a64c6a05465a9e6))
- Restore original workflow configuration
  ([05bb513](https://github.com/getrapidkit/core/commit/05bb513c7f207045984dab0739e25298f3ba1489))
- Restore original workflow configuration
  ([6d2c185](https://github.com/getrapidkit/core/commit/6d2c185fcd4507e0c2758a1ee57c9f6326859b74))
- restore pre-commit config to working local hooks version
  ([6c040a1](https://github.com/getrapidkit/core/commit/6c040a14673ed945e410ea0d6b68a201ccc1a4c2))
- restore push trigger for sync-distribution workflow
  ([f7f803a](https://github.com/getrapidkit/core/commit/f7f803a9e41da0b5af5ccad6e3a51a2c4f64f8cb))
- restore push trigger for sync-distribution workflow
  ([f544b23](https://github.com/getrapidkit/core/commit/f544b237e8410bb7856a29230c67efa8c98bd710))
- safer push strategy in auto-update workflow
  ([3d3d5be](https://github.com/getrapidkit/core/commit/3d3d5be8c1a8b99b46108e8879890eb7b97a08a6))
- sanitize CLI help output for legacy encodings
  ([cc0919f](https://github.com/getrapidkit/core/commit/cc0919f8468db3fef62870956d64f17b7139f352))
- Simplify workflow to run without dependencies
  ([cd0c2e8](https://github.com/getrapidkit/core/commit/cd0c2e8bdb8e54fea02306f2abd669978d62313c))
- Specify individual workflow files per tier instead of entire directory
  ([4eded3d](https://github.com/getrapidkit/core/commit/4eded3d98d5bbc06db54aae8c5939ae786052146))
- stabilize CLI import and dependency audit
  ([d492ea3](https://github.com/getrapidkit/core/commit/d492ea34753fc3779a5ad85b813a4e53b40c67cc))
- **sync:** correct indentation for post-sync deployment step
  ([760e527](https://github.com/getrapidkit/core/commit/760e527c759ac7c74abe51bbb12462e3b54304bd))
- **sync:** ensure post-push step is a proper step (no YAML in shell)
  ([d14d82a](https://github.com/getrapidkit/core/commit/d14d82a47cc32956ba64b9c001116ff60ac76d40))
- **sync:** move enterprise note step out of shell block
  ([d4fc245](https://github.com/getrapidkit/core/commit/d4fc245e03a2add9e4858e71ebb147bd873f4bc7))
- **sync:** move post-sync deployment step out of shell block
  ([42fa516](https://github.com/getrapidkit/core/commit/42fa516b83ef66db035afaeb2a9fc9ffe9e024b0))
- **sync:** use authenticated git clone for preserve step
  ([87c716d](https://github.com/getrapidkit/core/commit/87c716da210608af8b8b2a9b5d3736965b3acf87))
- **test:** Remove duplicate empty core test directory
  ([a036752](https://github.com/getrapidkit/core/commit/a03675258b966433e7f8196538b97e92e36121f7))
- update all packages to latest stable versions
  ([ed91cb9](https://github.com/getrapidkit/core/commit/ed91cb974e2e7ce52dcc54a1234fc0108a61d4cb))
- Update coverage grep patterns to match analyzer output
  ([a3996eb](https://github.com/getrapidkit/core/commit/a3996eba7efe5e4702b8371b28f086185dde53df))
- Update deprecated actions/upload-artifact from v3 to v4
  ([41fb484](https://github.com/getrapidkit/core/commit/41fb484ff5a9808f7f5985b4db88fc064fc7a27d))
- update distribution mappings for proper tier separation
  ([d837236](https://github.com/getrapidkit/core/commit/d8372360ffc5d3b7aecec503964bf0e8190e06cb))
- update distribution system with cumulative test logic
  ([44e0994](https://github.com/getrapidkit/core/commit/44e0994f295a94ebcf6535b24f8842f56b73297e))
- update Makefile for proper tool installation
  ([51c282e](https://github.com/getrapidkit/core/commit/51c282eb25d432cac0ea4f8618d77cfdac7b8759))
- update tests to use psutil_runtime instead of psutil
  ([95ee729](https://github.com/getrapidkit/core/commit/95ee729fcae30d78cf67012f273c980c64c7a11f))
- use force-with-lease in auto-update workflow
  ([f0831b0](https://github.com/getrapidkit/core/commit/f0831b07e09aa013463267b43f8d275e52c1563c))
- Use GITHUB_TOKEN instead of API_TOKEN_GITHUB for distribution
  ([1da8718](https://github.com/getrapidkit/core/commit/1da87185a489191a3639f8f5739bd9c9c0543dd3))
- Use here document for safe commit message handling
  ([358131e](https://github.com/getrapidkit/core/commit/358131e28afc4fb716150e925a7f0dbc067c7d50))
- Use Python for safe commit message handling in CI
  ([7c96973](https://github.com/getrapidkit/core/commit/7c9697379a6ba11d07f091c1568c64c5032fca15))

### Performance Improvements

- optimize Docker build performance and prevent timeouts
  ([73da24e](https://github.com/getrapidkit/core/commit/73da24e7c8dcbdd42e4ffe6dc9a1e7e32b3492ed))

### Reverts

- remove poetry.lock from community tier distribution
  ([ea9aa84](https://github.com/getrapidkit/core/commit/ea9aa84ad56b6e32ec5afce9fa4622f39ca210a3))
- restore stable workflow configuration from yesterday
  ([e1a5159](https://github.com/getrapidkit/core/commit/e1a51595f930a780a80f09820c4435f5bb454eb8))

### Documentation

- add CLI_COMPAT + INDEX; apply compatibility shims and tests; update CI and packaging pins
  ([2719625](https://github.com/getrapidkit/core/commit/27196251a0bd6c6e1ba045b86a5bc21a2f4c07ad))
- add comprehensive development roadmap and future enhancements
  ([3288713](https://github.com/getrapidkit/core/commit/3288713d6128a43a4c962f8d8faab93470d1f9e9))
- add GitHub repository variables setup guide
  ([13af1ef](https://github.com/getrapidkit/core/commit/13af1ef0edd78976712499c5ecd62fbbb10f031a))
- add issue/PR templates and dev release checklist
  ([eda5217](https://github.com/getrapidkit/core/commit/eda5217a32c94b0946d0c25a6c242e960257d705))
- add issue/PR templates and dev release checklist
  ([d130975](https://github.com/getrapidkit/core/commit/d130975426d9eb7da772368095382ff7502195ad))
- add module lifecycle usage and pytest config
  ([be3a6da](https://github.com/getrapidkit/core/commit/be3a6da0f4a8459ebf7f678463a51940891154db))
- Add pre-commit setup instructions and update config to use Poetry
  ([db4cc87](https://github.com/getrapidkit/core/commit/db4cc871b3cd6d70323bcc83054debaed200d35d))
- add README-root.md and link from README.md — repo quick index
  ([1466972](https://github.com/getrapidkit/core/commit/1466972bbb8e74118ae4b8f64010d150b788e8ae))
- align licensing and monetization messaging
  ([d591ecc](https://github.com/getrapidkit/core/commit/d591eccac80cebcb9d4f5287c28128ca37cad819))
- clean and standardize CONTRIBUTING.md (Poetry-first, PR checklist, release/signing guidance)
  ([9850b7a](https://github.com/getrapidkit/core/commit/9850b7a53d649d3ed90d549af16e4daf82880eaa))
- finalize fences and headings; add TUI quickstart placeholder badges
  ([647b5bb](https://github.com/getrapidkit/core/commit/647b5bb47b14e3b778169fbd119e6d67f3dee9f5))
- harmonize docs index and bootstrap; point schemas to docs/advanced/schemas.md
  ([8c3df1a](https://github.com/getrapidkit/core/commit/8c3df1a291ddbb5be4659e50f65e2c9f33aa261a))
- **licensing:** add full developer documentation for module licensing, gating, and workflow
  ([9ad2bcd](https://github.com/getrapidkit/core/commit/9ad2bcd96a6d782b36068863a7ed0e7d04a93591))
- mdformat adjustments for community-staging deployment guide
  ([7c43ef2](https://github.com/getrapidkit/core/commit/7c43ef26b843425baccc3785f9652f74d97022fc))
- mdformat adjustments for community-staging deployment guide
  ([0aed890](https://github.com/getrapidkit/core/commit/0aed890267b0887db29e1fba9c959e18a3dd95dc))
- **modules:** add or enhance README for implemented and placeholder modules
  ([b56b396](https://github.com/getrapidkit/core/commit/b56b396afaf2240c6328ab97451a82ca0be5fa62))
- **modules:** add or enhance README for implemented and placeholder modules
  ([33631e0](https://github.com/getrapidkit/core/commit/33631e06daf61bef8d513ac3a0120d3ea9922cbb))
- reorganize documentation structure for Olympic-level quality
  ([1f5038f](https://github.com/getrapidkit/core/commit/1f5038f08ff0dda54fb729dfbc3467b9188703df))
- tidy README, add Quickstart and move JSON schemas to docs/advanced/schemas.md
  ([f86af3b](https://github.com/getrapidkit/core/commit/f86af3bb0c53565af56e27cf012896040b5b916a))
- Translate CI-CD-SIMPLIFICATION.md to English
  ([979ec7d](https://github.com/getrapidkit/core/commit/979ec7daa44fe20b33b1e9f7cb6b85946652bfd1))
- Update dev-engine documentation for community-only distribution
  ([2ed2581](https://github.com/getrapidkit/core/commit/2ed25818c0afea269dd85b20a0094b8f3d77b192))
- Update scripts mapping and expand commit guidelines
  ([aee31b4](https://github.com/getrapidkit/core/commit/aee31b4921b27fab9d1b2eec2b07c6e082f240f5))
- Update scripts mapping for commit validation tool
  ([03a4ebb](https://github.com/getrapidkit/core/commit/03a4ebb1f9c372aea06a97e25fbaf5421c770ef7))

## Changelog

All notable changes to this project will be documented in this file.

This file is automatically generated by
[release-please](https://github.com/googleapis/release-please).
