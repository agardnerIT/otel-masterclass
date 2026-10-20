# OpenTelemetry Masterclass

Welcome! In this workshop you learn OpenTelemetry (OTel) by doing.
It takes 2-3 hours. You need your own laptop.

We start with the basics and move quickly. All code is open source, so you can repeat every lab at home.

## Agenda

| # | Section | Area | Type | Minutes |
|---|---|---|---|---|
| | [OTel overview](concepts.md) | Intro | Talk | 15 |
| 1 | [Auto instrumentation](labs/01-auto-instrumentation.md) | Generate | Lab | 15 |
| 2 | [Auto instrumentation expanded](labs/02-auto-expanded.md) | Generate | Lab | 15 |
| 3 | [Manual instrumentation](labs/03-manual-instrumentation.md) | Generate | Lab | 25 |
| 4 | [OTel Injector](labs/04-injector.md) | Generate | Discussion | 10 |
| 5 | [Collector basics](labs/05-collector-basics.md) | Collect and process | Lab | 20 |
| 6 | [Processors](labs/06-processors.md) | Collect and process | Lab | 25 |
| 7 | [Custom collector with OCB](labs/07-ocb.md) | Collect and process | Lab | 10-15 |
| 8 | [Semantic conventions](labs/08-semantic-conventions.md) | Standardise | Lab | 15 |
| 9 | [Weaver](labs/09-weaver.md) | Standardise | Lab | 20 |
| 10 | [Control plane: OpAMP](labs/10-opamp.md) | Control plane | Lab | 20 |
| 11 | [Bindplane](labs/11-bindplane.md) | Control plane | Discussion + Demo | 5 |
| | **Total** | | **~180** |

## Prerequisites

- A laptop with Docker, and Python 3.11+.
- Optional: a Dynatrace tenant and an API token. Without one, every lab has a console fallback.

Check your setup on the [Setup page](setup.md).

!!! tip "At the start of the workshop"
    Run the image download from [Setup, step 6](setup.md#6-download-the-lab-images-at-the-start-of-the-workshop) in a spare terminal and leave it running. It fetches about 3 GB, so it is better done while the slides are on than at the first lab.
