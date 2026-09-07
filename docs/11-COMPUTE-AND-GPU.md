# 11 — Compute: where a GPU belongs, and where it does not

## 11.1 The short answer

**The knowledge layer needs no GPU. Not a small one, not occasionally — none.**

Everything in `prototype/` is bookkeeping, statistics, and search over binned fields. It runs on
a laptop. The full calibration sweep — hundreds of cohorts through the hunter and the tribunal —
runs in minutes on four CPU cores with no dependencies beyond the Python standard library. There
is no model to train here and nothing to accelerate.

GPU belongs one plane down, in **P1 Measurement** and **P2 Representation**: the vision stack that
turns a slide into objects with coordinates. That system is being built separately, and it is the
only part of OP-OS with a real compute appetite.

So "connect a cloud GPU to build the prototype" solves a bottleneck that is not the bottleneck.
The bottleneck, in order, is:

1. **Instrument metadata capture** — organisational, zero compute, and the gate on everything.
2. **A validated canonical frame** — modest compute, hard validation work.
3. **Segmentation at archive scale** — this is where the GPU goes.

A team that buys GPU time before it has (1) will produce a large quantity of measurements that
can never clear a promotion gate, because the tribunal will have no channels to stratify on.

## 11.2 What actually needs a GPU, and how much

Sizes are for planning conversations, not procurement; measure your own stack before buying.

| Workload | Plane | Class of hardware | VRAM | Notes |
| --- | --- | --- | --- | --- |
| Nuclei/cell segmentation inference over WSIs | P1 | one modern 24 GB card (L4, A10G, RTX 4090-class) | 16–24 GB | Tiled inference. Minutes to tens of minutes per slide at 40×, dominated by tissue area and tile overlap |
| Tissue/epithelium region segmentation, basement-membrane detection for the φ frame | P2 | same card | 8–16 GB | U-Net-class. Cheap relative to nuclei |
| Pathology foundation-model embeddings (ViT-L/H class) | P2 | 24–48 GB | 24–48 GB | Inference only; highly batchable; the throughput here is I/O-bound more often than compute-bound |
| Fine-tuning a segmenter on your own annotations | P1 | 1–2 × 48 GB (L40S, A6000) or 1 × 80 GB | 48–80 GB | Episodic, not continuous. Rent this rather than own it |
| Frame-model training and validation | P2 | 24 GB | 24 GB | Small models, lots of iterations |
| **The entire knowledge layer** | P0, P3–P9 | **CPU** | — | Ledger, hunter, tribunal, calibration range, store |

Two sizing realities that catch people out:

- **Storage and I/O dominate, not FLOPs.** A 40× WSI is roughly 1–4 GB. A 3,000-case archive is
  3–12 TB before masks and features. The normal failure mode is an expensive GPU sitting idle
  waiting on network storage. Put fast local NVMe scratch next to the GPU and keep the object
  store in the same region; a cheaper GPU with good I/O beats a better GPU without it.
- **This workload is embarrassingly parallel and interruptible.** Segmentation over an archive is
  a queue of independent slides. That makes spot/preemptible instances genuinely appropriate here,
  which is unusual and worth exploiting — it typically cuts the cost by 60–80%.

## 11.3 Choosing where to run it — compliance decides, not price

Whole-slide images are patient data. Where they may be processed is an institutional question
that must be settled **before** any code, because it constrains everything downstream.

| Option | When it is right | The catch |
| --- | --- | --- |
| **On-prem workstation** — one box, RTX 6000 Ada / 4090-class | A single lab, archive under ~10 TB, data that should not leave the building | One-time cost, no egress, no compliance negotiation. Usually the correct answer at this stage and the one people skip past |
| **Institutional HPC cluster** | Your university or hospital has one | Cheapest per hour and already covered by existing data agreements. Slow to get access; scheduler queues; often stale drivers |
| **Hyperscaler (AWS / GCP / Azure)** | Identifiable data must leave the building | BAAs and the compliance paperwork exist. Expensive; watch egress charges, which are where WSI budgets die |
| **GPU rental (Lambda, RunPod, Vast, etc.)** | De-identified or synthetic data, bursty fine-tuning | Cheap per hour, weak compliance story. **Do not put identifiable slides on these** without an explicit institutional sign-off you can point to |

Recommendation for a lab at this stage: **one on-prem box for continuous inference, plus rented
capacity for episodic fine-tuning on de-identified data.** It keeps the routine path off the
compliance critical path and rents only the part that is genuinely bursty.

## 11.4 What this session can and cannot do

Plainly: this container has no GPU and no credentials for any cloud account, and provisioning
infrastructure on your behalf would mean handling your cloud credentials, which is not something
to do casually in a chat session. What is useful from here is the specification above, and code
written to a boundary the GPU work can plug into without touching the kernel.

## 11.5 The boundary, and it is deliberately not a Python interface

The vision stack meets the knowledge layer at a **file contract**, not an API:

```
objects.csv     specimen_id, object_id, phi, <quantity columns...>
specimens.csv   specimen_id, scanner_id, scanner_model, mpp, objective,
                stain_protocol, stain_lot, fixation_delay_h,
                section_thickness_um, lab_id, pipeline_version, ...
quantities.csv  quantity, mask_source, sigma_log
```

Any segmentation stack — anything in Python, a CUDA service, a commercial platform, a
pathologist with a spreadsheet — that can emit those three files plugs straight in:

```bash
python3 prototype/cli.py ingest --db opos.db --dir /path/to/output
python3 prototype/cli.py hunt   --db opos.db
```

A file contract rather than a class hierarchy is the right boundary here for three reasons: the
vision stack is being built by different people on a different schedule, its output is
reproducible evidence that should be archived anyway, and it keeps the GPU half and the CPU half
independently replaceable. The version hash of the vision stack travels in `pipeline_version`,
which is what binds every downstream claim to the instrument that produced it (`docs/00` I5).

`mask_source` is not decoration. It is the field that lets the tribunal kill invariants
manufactured by two features sharing a segmentation mask — the dominant false positive in this
domain, and the one the demo shows scoring highest of all candidates.

## 11.6 Order of work, honestly

1. **Metadata capture into `specimens.csv`.** No GPU. Weeks of process change. Blocks everything.
2. **Frame validation.** Modest GPU. Does φ reproduce across serial sections? Where does it fail —
   rete pegs, tangential cuts? This decides whether any field is trustworthy.
3. **Measurement models.** Repeat scans, inter-scanner panels, manual annotation subsets. Mostly
   tedium, some GPU. Without these the noise-floor channel cannot run.
4. **Segmentation at scale.** Now the GPU earns its keep.
5. **Knowledge layer against real fields.** CPU, and already built.

Steps 1–3 are where the project succeeds or fails, and none of them is a compute problem.
