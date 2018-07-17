# Introduction

This is a library for laying out non-overlapping text labels in [plotly](https://plot.ly).

# Usage

The simplest interface is to use `plotly_non_overlap_text` and pass
a `Scatter` and `Layout` object to it. The function will figure out
the correct placement for labels and update the `Layout` object
with `annotations`.

The function will respect the `markersize`, `color` and `fontsize`
arguments from your `Scatter` plot, but it will also update the
`Scatter` object with default values if they're not provided.

The function will respect the `x(y)axis range`, `margin` and
`width/height` arguments from your `Layout` object, but it will also
update the `Layout` object with default values if they're not
provided.

# Other functions

There are other various lower level functions.

