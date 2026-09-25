# Phase 9 Plan: Spec And Domain Shape Alignment

## 1. Shared Terminology

1. Define the canonical meaning of institution, tag, aggregation dimension, single-month aggregation, history aggregation, and compatibility reporting.
2. Align those terms with the constitution documents so later specs and implementation phases use one vocabulary.
3. Record what this phase intentionally does not decide yet.

## 2. Institution Spec Baseline

1. Define the initial institution field shape and uniqueness expectations.
2. Specify the initial optional account-to-institution relationship.
3. Capture migration expectations that preserve existing accounts without forced reassignment.

## 3. Tag Spec Baseline

1. Define the initial tag field shape and uniqueness expectations.
2. Specify the initial zero-to-many account-to-tag relationship.
3. Capture the expectation that tags remain reusable reference data for grouping and reporting.

## 4. Reporting Boundary Alignment

1. Define the reporting vocabulary that later aggregation phases must use.
2. Separate terminology decisions from deferred implementation decisions.
3. Record the expectation that existing report commands should converge on one shared aggregation model where practical.

## 5. Follow-On Phase Readiness

1. Leave enough clarity for Phase 10 institution schema work without over-specifying later CLI behavior.
2. Leave enough clarity for Phase 13 tag schema work without prematurely deciding tag management semantics.
3. Leave enough clarity for Phases 16 through 19 reporting work without drafting those feature specs in full.
