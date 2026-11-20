# ForgeCommerce Agent Guide

ForgeCommerce is a locally runnable, multi-tenant commerce platform. Keep changes inside this repository, preserve tenant isolation, and add a focused test for every behavior change.

## Development

The platform intentionally uses Python's standard library for the first local staging slice so it can run on the target host without an external package registry. Run `python3 -m unittest discover -s tests -v` before committing and start the app with `python3 -m forgecommerce.app`.

## Checkpoints

Update `progress/CURRENT_STATE.json`, `progress/PROGRESS.md`, `progress/TEST_RESULTS.md`, and the daily report after each verified milestone. Never mark a feature VERIFIED without executable evidence.
