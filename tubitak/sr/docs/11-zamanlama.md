# WP11 — timings for the cold-start walkthrough, with a citable origin

## 1. Why this document exists

A walkthrough was run some packages ago and its timings — plugin zip 0.4 s, model 8.7 s,
CLC+ Türkiye 44.8 s, OSM 24 s, generation 8.32 min — were **reported in chat and never
written to a file.** `git grep` and `git log -S` confirm no such figure has ever existed in
any tracked file in this repository.

That matters because a presentation was about to cite **"zero to a generated scene in about
ten minutes"** on the strength of it. A number whose only source is a conversation cannot be
checked by the person who has to defend it.

**The walkthrough was therefore re-run rather than reconstructed**, because re-running is
cheaper than arguing about what a transcript meant, and it produces conditions that can be
stated. Everything below was measured on **31 August 2026**.

## 2. Conditions — the part the original number was missing

| | |
|---|---|
| Date | **2026-08-31**, 10:25–11:05 +03 |
| Machine | Mac16,6 — **Apple M4 Max**, 14 cores (10 performance + 4 efficiency), **36 GB** RAM |
| OS | macOS **26.5.1** (25F80) |
| QGIS | **4.2.1 (Belém do Pará)** |
| Network | **Wi-Fi 802.11ax**, 2.4 GHz channel 11, 20 MHz, signal −78 dBm / noise −92 dBm, reported link rate 97 Mbit/s |
| Latency | `objects.githubusercontent.com` **35.3 ms** mean over 5 pings (min 30.4, max 43.4); `github.com` 65.6 ms |
| Profile | a throwaway QGIS profile outside the normal profiles root; the default profile was hashed before and after and is byte-identical |

**Measured throughput exceeded the reported link rate** (23.6 MB/s on the model against a
97 Mbit/s ≈ 12 MB/s nominal), so the interface's advertised rate is not a usable predictor
here. The per-file rates below are the real conditions.

## 3. Downloads — from the published release URLs, unauthenticated

Each file fetched fresh with `curl` from the URL the README prints, then checksum-verified.

| File | Bytes | **Measured** | Rate | Chat figure | Δ |
|---|---|---|---|---|---|
| `gencp_plugin.zip` | 94,987 | **0.548 s** | 0.17 MB/s | 0.4 s | +37 % |
| `gencp_C2_fp32.onnx` | 217,678,087 | **9.234 s** | 23.6 MB/s | 8.7 s | +6 % |
| `clcplus_2021_turkey_10m.tif` | 916,422,550 | **47.424 s** | 19.3 MB/s | **44.8 s** | **+6 %** |
| `turkey-2026-08-19.osm.pbf` | 642,343,710 | **39.485 s** | 16.3 MB/s | 24 s | **+65 %** |
| **total** | **1,776,539,334** | **96.69 s = 1.61 min** | | ~78 s | |

Integrity after download: CLC+ `sha256 a41b6fac…73de0` and OSM `md5 76af5efb…402a`, both
matching the values published in the release notes.

**Three of the four reproduce within 6 %.** The 44.8 s figure at issue is confirmed: 47.4 s
today, on a different day and a different Wi-Fi channel.

**The OSM figure does not reproduce, and the likely reason is that it is not the same
download.** 24 s for 642 MB is 26.8 MB/s. The plugin's own button tries **Geofabrik first**
and falls back to our pinned mirror only when Geofabrik will not serve; the walkthrough
almost certainly measured Geofabrik, while this run measured the GitHub mirror. Two hosts,
two numbers. **This is exactly what an unwritten timing loses: not the digits, but which
thing was timed.**

## 4. Install

Unpacking `gencp_plugin.zip` into the profile's plugin directory: **0.016 s.** Negligible,
and it is the whole of "installation" once the file is on disk — QGIS's *Install from ZIP*
does the same unpack.

## 5. Generation — and why one number cannot describe it

Extent, stated because it is part of the measurement: **10.31 km × 10.22 km** over Istanbul,
EPSG:32635, `(659627.8, 4538275.3, 669941.4, 4548493.6)`. **30 tiles**, output
1032 × 1022 × 3, valid fraction 0.99999, **`workers=1`**.

| Run | Total | render | infer | mosaic |
|---|---|---|---|---|
| **cold** — first ever, country-wide PBF, empty cache | **997.08 s = 16.62 min** | 22.50 s | 0.46 s | 0.29 s |
| **warm** — same extent, same work directory | **1.29 s** | 0.00 s | 0.45 s | 0.28 s |

**The three reported stages account for 23.25 s of the cold run's 997 s.** The remaining
**≈ 974 s (16.2 min, 97.7 % of the run)** elapses inside `generate()` before the first render
callback fires. The dominant work there is preparing the OSM source — parsing and indexing
the **642 MB country-wide extract** — which is consistent with the warm run, where every tile
was already rendered and the OSM source was never touched at all.

*Attribution stated honestly: the 974 s is measured as a gap between instrumented stages, not
separately instrumented. That it is OSM preparation is inferred from where it sits in the
call and from the warm run skipping it entirely.*

## 6. What the presentation should say instead

**"Zero to a generated scene in about ten minutes" is not supported by any run measured
here.** The two runs that exist are 16.6 minutes and 1.3 seconds, and which one a viewer gets
depends on things the sentence does not mention.

Defensible forms, each with its condition attached:

> **Downloading all four files takes about 1.6 minutes** (1.78 GB, measured 2026-08-31 on a
> 20 MB/s connection). Download time scales with the connection and is not a property of the
> software.

> **First generation of a 10 × 10 km scene takes about 17 minutes** on an M4 Max, single
> worker, when the OSM source is the 642 MB country-wide extract and nothing is cached.

> **Re-generating the same scene takes about 1 second**, because rendered tiles are cached.

If a single headline number is wanted, **"about 20 minutes from nothing to a first scene"**
(1.6 min downloads + 16.6 min cold generation) is the one this run supports — and the demo on
4 September will not experience it, because that machine's caches are already warm.

## 7. What could not be reconstructed

1. **The original walkthrough's extent is unknown.** Its 8.32 min generation cannot be
   compared with the 16.62 min here, because scene size, worker count, PBF size and cache
   state all move that number and none of them was recorded. The comparison is not made.
2. **Which host served the original OSM download is unknown** (§3).
3. **The original network conditions are unrecoverable.** This is the whole finding.

## 8. The finding, in general form

> **A measurement that exists only in a conversation has no conditions attached to it, and
> conditions are most of what a timing is.**

The digits survived the transcript — 44.8 s reproduced within 6 %. What did not survive was
the extent, the worker count, the cache state, and which server the bytes came from. Three of
those four turn out to matter more than the digits: they are the difference between 16.6
minutes and 1.3 seconds.

Standing practice 2 already requires the inference path of every number. This is the same
rule for wall-clock: **a timing is written with its machine, its network and its inputs, or it
is not written at all.**
