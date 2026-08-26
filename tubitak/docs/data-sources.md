# Consolidated data-source and reproducibility record

**Updated:** 2026-08-19. One table for every external dataset the Turkish pipeline depends on.
All large files live under gitignored `tubitak/data/` (Geofabrik under
`tubitak/data/geofabrik/`, weights under `GenCP_HR_demo/checkpoints/`).

| product | version / snapshot | source | md5 | size |
|---|---|---|---|---|
| Geofabrik `austria-latest` | data 2026-08-18T20:20:57Z | download.geofabrik.de/europe/ | e864ed7a5fbcb65ae57c131718cb9bf0 | 785 M |
| Geofabrik `belgium-latest` | data 2026-08-18T20:20:57Z | 〃 | b4151f785875aa156cf28b55c9614dbb | 672 M |
| Geofabrik `france-latest` | data 2026-08-18T20:20:57Z | 〃 | 3d1c462f48e3cc89b35b8be88b399ac6 | 4.7 G |
| Geofabrik **`germany-260817`** | **data 2026-08-17T20:21:36Z** | 〃 | a9dc28f754e5df792f11f9a74a5d9592 | 4.5 G |
| Geofabrik `great-britain-latest` | data 2026-08-18T20:20:57Z | 〃 | 2115b4be7c92694fed4edd500aab3bdb | 2.0 G |
| Geofabrik `hungary-latest` | data 2026-08-18T20:20:57Z | 〃 | bbbaa9e50217c76283ce2591c0c4d4a4 | 320 M |
| Geofabrik `italy-latest` | data 2026-08-18T20:20:57Z | 〃 | eadcc482823ddc828eed8d0bef26c071 | 2.1 G |
| Geofabrik `serbia-latest` | data 2026-08-18T20:20:57Z | 〃 | 2afe76148cff7bdfe389c48e9ebf398a | 240 M |
| Geofabrik `spain-latest` | data 2026-08-18T20:20:57Z | 〃 | dd95ee8d01c0d2e84f98428cb38efc2d | 1.4 G |
| Geofabrik `sweden-latest` | data 2026-08-18T20:20:57Z | 〃 | 5436785bbddb25ac02c597c360814d6a | 784 M |
| Geofabrik **`turkey-latest`** | data 2026-08-18T20:20:57Z | 〃 | 76af5efb51c5ef9fcb738795753a402a | 625 M |
| Sentinel-2 TCI | S2C_36TVK_20260430_0_L2A (acq. 2026-04-30, cloud 2.04 %) | sentinel-cogs S3 (Element84 Earth Search) | b163f09ceb6ff435846ea61a20b8b7b0 | 341 M |
| Sentinel-2 SCL | same product | 〃 | e6706fd2d8cec2e737678e3cba2480d9 | 5.1 M |
| ESA WorldCover | v200 (map year 2021) | esa-worldcover S3 (windowed remote reads; no local archive file) | — (per-tile COGs) | ~0 local |
| **CLC+ Backbone** | 2021, V1_1, `CLMS_CLCplus_RASTER_2021`, GeoTIFF | CLMS (ordered 2026-08-19, **pending delivery**) | — (fill on arrival) | ~7 G |
| GenCP HR weights (RGB) | Zenodo 15044428, `genCP_HR_RGB_model/latest_net_G.pth` | zenodo.org/records/15044428 | 1e5176ef95d3b98ae56ff716b2219ea5 | 208 M |
| GenCP HR weights (B04) | same record | 〃 | f2eef88970f396bd6075eb5d0e84eb21 | 208 M |
| GenCP HR corpus | Zenodo 15044428, `GenCP_HR_DB.zip` | 〃 | d7001c7062aa63901dac591211c76724 | 1.6 G |

**Caveat on "one coherent snapshot":** ten Geofabrik extracts share the data timestamp
2026-08-18T20:20:57Z; **Germany is pinned one day earlier (2026-08-17)** because its `-latest`
file could not be checksum-verified during the daily-update race (osm-palette.md §10). Any
cross-border analysis touching Germany carries a one-day OSM drift.

**Accepted limitation — the OSM/imagery temporal gap.** The OSM snapshot is 2026-08-18; the Ankara
acquisition is 2026-04-30 — a gap of roughly four months. Features mapped or built in between will
appear in the rendered input and not in the imagery. This is the same class of error as the
measured hallucination failure mode (an input edge with no real-world counterpart at acquisition
time), bounded and documented rather than eliminated. It is one more reason KARIOS results on
Turkish chips must be read against the chip-level information scores.
