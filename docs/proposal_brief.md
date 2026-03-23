# Proposal Brief

## Title

Xarray SQL Bridge for Lumen AI

## Problem

Lumen's AI transform flow is strongest for SQL-capable sources, but many scientific and geospatial datasets are stored as `xarray.Dataset`. That leaves a gap between Lumen's strongest AI pathway and the data model commonly used for multidimensional scientific data.

## Core idea

Implement an xarray-backed `BaseSQLSource` using `xarray-sql`, so the existing `SQLAgent` can write filters, aggregations, and derived transforms against xarray-backed data without introducing a second transform system.

## Why this is interesting

- It reuses Lumen's existing SQL AI path instead of adding another agent path.
- It brings scientific array data into the same transform workflow as tabular sources.
- It identifies a concrete integration strategy rather than proposing generic "AI for xarray" support.

## Prototype novelty

The key insight is to register each xarray `data_var` as its own logical SQL table.

That preserves mixed-dimensional datasets while still giving the AI a table-oriented abstraction it already understands.

## What the prototype already proves

- xarray-backed data can satisfy the `BaseSQLSource` contract
- Lumen's SQL path is a viable integration point for AI-written transforms over xarray-backed data
- mixed-dimensional xarray datasets can still be queried by treating variables as separate logical tables

## What remains after the prototype

- broader prompt evaluation with live models
- more backend dialect validation
- better treatment of auxiliary coordinates
- decisions about coexistence with `XarraySource` and `XarrayAgent`

## Why this proposal stands out

This is not just a feature request. It is a working architectural prototype with:

- code
- tests
- a demo
- explicit constraints
- a clear path from feasibility to hardening
