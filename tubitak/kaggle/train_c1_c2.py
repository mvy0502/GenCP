# Kaggle notebook script - Phase C arms C1 (GAN+L1) and C2 (L1-only)
# Dataset "gencp-tr" mounted at /kaggle/input/gencp-tr
# Full rationale: tubitak/docs/phase-c-config.md ; registration: phase-c-registration.md
#
# ---------------------------------------------------------------------------------------
# CHANGELOG 19 Aug 2026 - Kaggle bring-up. Reasoning recorded in phase-c-config.md.
#
#   1. preflight()            Assert from inside the running kernel that a CUDA device is
#                             actually visible and that the dataset is actually mounted,
#                             before anything expensive starts. The metadata claiming
#                             enable_gpu is not evidence that torch can see a GPU.
#
#   2. make_cold_start_D()    No discriminator was ever released for these weights.
#                             --continue_train makes base_model.setup() call
#                             load_networks('latest'), which loops over model_names
#                             ['G','D'] and calls torch.load() with NO existence check.
#                             Without a latest_net_D.pth the run dies before iteration 1.
#                             D is therefore built here, through the repository's own
#                             define_D -> init_net -> init_weights path, seeded, and its
#                             provenance is written next to it and printed every run.
#
#   3. "--seed","42" removed  This fork has no --seed option anywhere in options/, and
#                             BaseOptions.gather_options() ends in parser.parse_args()
#                             (strict), so argparse would exit 2 with
#                             "unrecognized arguments: --seed 42" on the FIRST call of
#                             both arms. Seeding moved to install_seed_hook() below,
#                             which seeds the training process itself. The seed is not
#                             dropped; it is applied where it can actually take effect.
#
#   4. "--print_freq","10"    Logging only, no effect on the optimisation. At batch 4 there
#                             are 1394 iterations per epoch, so the default print_freq 100
#                             yields 3-4 rows over the first few hundred iterations, which
#                             is precisely the window the cold-start stop rule watches.
#
#   5. torchmetrics guard     models/pix2pix_model.py imports torchmetrics at module level
#                             and constructs LearnedPerceptualImagePatchSimilarity(...).cuda()
#                             unconditionally in __init__, NOT only under --LPIPS. It is not
#                             in requirements.txt, so its presence is checked here.
#
#   NO hyperparameter was changed. lr, n_epochs, n_epochs_decay, epoch_count, batch_size,
#   load_size, crop_size, direction, netG, norm, model, save_epoch_freq and the two-stage
#   C1 warm-up structure are byte-identical to the version registered in phase-c-config.md.
# ---------------------------------------------------------------------------------------

import os, subprocess, shutil, sys, hashlib, datetime, re, statistics

ARM  = os.environ.get("ARM", "C1")            # "C2" = L1-only arm; "C3" = C2 + ~20% EU pairs
                                              # "C4" = GAN + LPIPS (C1 protocol); "C5" = LPIPS-only
                                              # (C2 protocol). Registration: phase-c-lpips-registration.md
ROOT = "/kaggle/working/GenCP"
DATA = None                                   # resolved below by resolve_data_dir()
SEED = int(os.environ.get("SEED", "42"))      # recorded in every log line and provenance file.
                                              # Seeds 43+ are the replication package
                                              # (seed-replication-registration.md): the seed is
                                              # the ONLY manipulated factor, and it varies the
                                              # cold-D draw in the adversarial arms by intent.
                                              # 42 remains the default so a re-push of the
                                              # original kernels is byte-identical in behaviour.

BAR = "=" * 78


def resolve_data_dir():
    """Find the mounted gencp-tr dataset instead of assuming where Kaggle put it.

    `/kaggle/input/<slug>` is not guaranteed. On the image this project draws (19 Aug 2026)
    a private dataset attached through `dataset_sources` mounts at
    `/kaggle/input/datasets/<owner>/<slug>`, which is why the first C1 push died in preflight
    while the dataset was correctly attached and `ready`. That failure was previously recorded
    as "fixed by dataset_sources"; it was not - the attachment was never the problem, the
    hard-coded path was.

    Both layouts are accepted, and if Kaggle moves the mount again this finds it by locating
    the payload rather than by guessing another path.
    """
    import glob
    for c in ("/kaggle/input/gencp-tr",
              "/kaggle/input/datasets/vedatyildirim/gencp-tr"):
        if os.path.isdir(os.path.join(c, "pairs", "train")):
            return c
    hits = sorted(glob.glob("/kaggle/input/**/pairs/train", recursive=True))
    return os.path.dirname(os.path.dirname(hits[0])) if hits else None


DATA = resolve_data_dir()


def log_environment():
    """Record the full environment at preflight, every run, on every platform.

    Corrections-log entry 29: the invariance table listed "same image" as a held invariance
    for this whole package, but NO run ever captured what the image contained - only torch
    and torchmetrics were printed. The claim was therefore unfalsifiable, which is exactly
    what standing practice 1 exists to prevent. From here on the image is a recorded fact,
    so a later run can be diffed against an earlier one instead of assumed equal to it.
    """
    print(BAR, flush=True)
    print(f"[env] python {sys.version.split()[0]}  executable {sys.executable}", flush=True)
    for mod in ("torch", "torchvision", "torchmetrics", "numpy", "PIL", "scipy"):
        try:
            m = __import__(mod)
            print(f"[env] {mod}=={getattr(m, '__version__', '?')}", flush=True)
        except Exception as exc:
            print(f"[env] {mod} import failed: {exc}", flush=True)
    try:
        import torch
        print(f"[env] torch.version.cuda={torch.version.cuda}  "
              f"cudnn={torch.backends.cudnn.version()}", flush=True)
    except Exception as exc:
        print(f"[env] torch cuda/cudnn probe failed: {exc}", flush=True)
    for k in sorted(os.environ):
        if any(s in k.upper() for s in ("KAGGLE_DOCKER", "IMAGE_TAG", "MODAL_IMAGE")):
            print(f"[env] {k}={os.environ[k]}", flush=True)
    fr = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                        capture_output=True, text=True).stdout.strip()
    print("[env] pip freeze BEGIN", flush=True)
    for line in fr.splitlines():
        print(f"[env]   {line}", flush=True)
    print(f"[env] pip freeze END ({len(fr.splitlines())} packages)", flush=True)


def preflight():
    """Verify the two things the metadata cannot prove: a real GPU and a real mount."""
    import torch
    log_environment()
    print(BAR, flush=True)
    print(f"[preflight] arm={ARM}  seed={SEED}  "
          f"utc={datetime.datetime.now(datetime.timezone.utc).isoformat()}", flush=True)
    print(f"[preflight] torch={torch.__version__}  "
          f"cuda_available={torch.cuda.is_available()}", flush=True)
    if not torch.cuda.is_available():
        raise SystemExit(
            "[preflight] FATAL: torch.cuda.is_available() is False. The accelerator is off "
            "for this session. Notebook settings -> Accelerator -> GPU, then re-run. "
            "Nothing was written.")
    cap = torch.cuda.get_device_capability(0)
    arches = torch.cuda.get_arch_list()
    print(f"[preflight] device={torch.cuda.get_device_name(0)}  "
          f"count={torch.cuda.device_count()}  capability={cap}", flush=True)
    print(f"[preflight] torch arch list={arches}", flush=True)

    # cuda_available=True is NOT sufficient. The first C1 push landed on a Tesla P100
    # (sm_60) under this image's torch 2.10.0+cu128, which builds for sm_70 and up. CUDA
    # reported available, the device reported healthy, and every kernel launch would have
    # failed at the first conv. Assert the arch is one this torch can actually emit code for.
    sm = f"sm_{cap[0]}{cap[1]}"
    if sm not in arches:
        raise SystemExit(
            f"[preflight] FATAL: {torch.cuda.get_device_name(0)} is {sm}, which this torch "
            f"({torch.__version__}) cannot generate code for; it supports {arches}. "
            "cuda_available was True and the device was visible - this is the trap. "
            "Set \"machine_shape\": \"NvidiaTeslaT4\" in kernel-metadata.json and re-push. "
            "Nothing was written.")
    print(f"[preflight] arch OK: {sm} is in the torch arch list", flush=True)

    if DATA is None or not os.path.isdir(DATA):
        listing = []
        for root, dirs, files in os.walk("/kaggle/input"):
            if root.count("/") - 2 > 4:
                dirs[:] = []
                continue
            listing.append(f"    {root}  [{len(dirs)} dirs, {len(files)} files]")
        raise SystemExit(
            "[preflight] FATAL: could not locate the gencp-tr payload under /kaggle/input. "
            "Attaching the dataset is necessary but not sufficient - the mount path is not "
            "guaranteed to be /kaggle/input/gencp-tr. What is actually mounted:\n"
            + "\n".join(listing or ["    <nothing under /kaggle/input>"])
            + "\nNothing was written.")
    print(f"[preflight] dataset resolved to: {DATA}", flush=True)
    n_pairs = len(os.listdir(f"{DATA}/pairs/train"))
    print(f"[preflight] mount OK: {DATA} -> {sorted(os.listdir(DATA))}", flush=True)
    print(f"[preflight] training pairs: {n_pairs}", flush=True)
    if not os.path.isfile(f"{DATA}/latest_net_G.pth"):
        raise SystemExit(f"[preflight] FATAL: {DATA}/latest_net_G.pth missing.")
    print(BAR, flush=True)


def install_seed_hook():
    """Seed the training subprocess without modifying the repository.

    train.py runs in its own interpreter, so seeding in this process would not reach it,
    and this fork exposes no --seed option. Python imports a module named `sitecustomize`
    automatically at interpreter start-up (stdlib `site`), so placing one on PYTHONPATH
    seeds random/numpy/torch before train.py constructs anything. It prints a line so the
    log proves the hook actually fired.
    """
    d = "/kaggle/working/_seedhook"
    os.makedirs(d, exist_ok=True)
    with open(f"{d}/sitecustomize.py", "w") as f:
        f.write(
            "import random, numpy, torch\n"
            f"SEED = {SEED}\n"
            "random.seed(SEED)\n"
            "numpy.random.seed(SEED)\n"
            "torch.manual_seed(SEED)\n"
            "torch.cuda.manual_seed_all(SEED)\n"
            "print('[seed-hook] random/numpy/torch seeded with %d' % SEED, flush=True)\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = d + ((os.pathsep + env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
    return env


def make_cold_start_D(ck):
    """Create the randomly initialised discriminator this run starts from.

    Built with exactly the call Pix2PixModel.__init__ makes:
        networks.define_D(opt.input_nc + opt.output_nc, opt.ndf, opt.netD,
                          opt.n_layers_D, opt.norm, opt.init_type, opt.init_gain, gpu_ids)
    with this run's values: input_nc=3 and output_nc=3 (base_options defaults) -> 6,
    ndf=64, netD='basic', n_layers_D=3 (base_options defaults), norm='batch' (passed on the
    command line and also the pix2pix default), init_type='normal' and init_gain=0.02
    (base_options defaults, the scheme used in the pix2pix paper), gpu_ids=[0].

    Saved the way base_model.save_networks saves it: the unwrapped module's CPU state_dict,
    so load_networks can read it back without a DataParallel key prefix.
    """
    sys.path.insert(0, ROOT)
    import torch
    from models import networks

    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    netD = networks.define_D(3 + 3, 64, "basic", 3, "batch", "normal", 0.02, [0])
    module = netD.module if hasattr(netD, "module") else netD
    state = module.cpu().state_dict()
    path = f"{ck}/latest_net_D.pth"
    torch.save(state, path)

    # Round-trip check: a fresh define_D must accept these keys, otherwise load_networks
    # would fail later with a much less obvious message.
    probe = networks.define_D(3 + 3, 64, "basic", 3, "batch", "normal", 0.02, [0])
    (probe.module if hasattr(probe, "module") else probe).load_state_dict(state)

    n_params = sum(p.numel() for p in state.values())
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    note = f"""latest_net_D.pth in this directory was NOT released with the GenCP weights.
No discriminator has ever been published for the GenCP HR model.

It was randomly initialised by tubitak/kaggle/train_c1_c2.py at the start of the run
recorded below, through the repository's own networks.define_D -> init_net -> init_weights
path, so that it starts in the distribution the training loop expects.

  created (UTC) : {datetime.datetime.now(datetime.timezone.utc).isoformat()}
  arm           : {ARM}
  seed          : {SEED}  (torch.manual_seed + torch.cuda.manual_seed_all, immediately before define_D)
  init scheme   : normal, gain 0.02  (init_type='normal', init_gain=0.02 - framework default)
  architecture  : define_D(input_nc=6, ndf=64, netD='basic', n_layers_D=3, norm='batch')
  parameters    : {n_params}
  sha256        : {sha}
  paired with   : latest_net_G.pth, the released GenCP HR RGB generator (genuinely pretrained)

Do not cite, publish, redistribute or reuse this file as a pretrained discriminator.
Any result produced from it starts from a cold, random D by design; see
tubitak/docs/phase-c-config.md, "Discriminator cold-start".
"""
    with open(f"{ck}/DISCRIMINATOR_PROVENANCE.txt", "w") as f:
        f.write(note)
    return note


def banner(note):
    """Printed at the top of every training invocation that uses the cold-start D."""
    print(BAR, flush=True)
    print("COLD-START DISCRIMINATOR - PROVENANCE", flush=True)
    print(BAR, flush=True)
    print(note, flush=True)
    print(BAR, flush=True)


preflight()

subprocess.run(["git","clone","--depth","1","-b","tubitak-tr",
                "https://github.com/mvy0502/GenCP.git", ROOT], check=True)
subprocess.run([sys.executable,"-m","pip","install","-q","dominate","visdom"], check=False)

# models/pix2pix_model.py imports torchmetrics at module level and calls .cuda() on an
# LPIPS metric in __init__ regardless of --LPIPS, but torchmetrics is not in
# requirements.txt. --no-deps so pip cannot swap the image's torch build out from under us.
try:
    import torchmetrics
    print(f"[deps] torchmetrics {torchmetrics.__version__} already in the image", flush=True)
except ImportError:
    print("[deps] torchmetrics missing from the image, installing with --no-deps", flush=True)
    subprocess.run([sys.executable,"-m","pip","install","-q","--no-deps",
                    "torchmetrics","lightning-utilities"], check=True)

os.makedirs(f"{ROOT}/datasets/tr/train", exist_ok=True)
for f in os.listdir(f"{DATA}/pairs/train"):
    dst = f"{ROOT}/datasets/tr/train/{f}"
    if not os.path.lexists(dst):
        os.symlink(f"{DATA}/pairs/train/{f}", dst)
if ARM == "C3":
    # C3 = winning arm (C2, L1-only) + the packaged 1200-pair EU reserve:
    # 1200/(5577+1200) = 17.7% of the mix, the registration's "~20% European corpus pairs".
    # eu_ prefix guards against any stem collision with the Turkish pairs.
    n_eu = 0
    for f in os.listdir(f"{DATA}/eu_pairs"):
        dst = f"{ROOT}/datasets/tr/train/eu_{f}"
        if not os.path.lexists(dst):
            os.symlink(f"{DATA}/eu_pairs/{f}", dst)
        n_eu += 1
    print(f"[C3] mixed in {n_eu} EU reserve pairs "
          f"({n_eu/(5577+n_eu):.1%} of the fine-tuning set)", flush=True)
ck = f"/kaggle/working/checkpoints/{ARM}"     # persistent output
os.makedirs(ck, exist_ok=True)
shutil.copy(f"{DATA}/latest_net_G.pth", f"{ck}/latest_net_G.pth")

PROVENANCE = make_cold_start_D(ck)            # writes latest_net_D.pth + the note beside it
banner(PROVENANCE)
ENV = install_seed_hook()

if ARM in ("C2", "C3"):                       # L1-only: zero the GAN term (Kaggle copy only)
    p = f"{ROOT}/models/pix2pix_model.py"
    s = open(p).read()
    needle = "self.loss_G = self.loss_G_GAN + self.loss_G_L1"
    assert s.count(needle) == 1, "C2 patch target not found exactly once - refusing to run"
    s = s.replace(needle,
        "self.loss_G = 0.0 * self.loss_G_GAN + self.loss_G_L1   # C2: L1-only arm")
    open(p, "w").write(s)
    print("[C2] adversarial term zeroed in the Kaggle copy of pix2pix_model.py", flush=True)

if ARM == "C5":                               # LPIPS-only: same patch, LPIPS branch (Kaggle copy only)
    p = f"{ROOT}/models/pix2pix_model.py"
    s = open(p).read()
    needle = "self.loss_G = self.loss_G_GAN + self.loss_G_LPIPS"
    assert s.count(needle) == 1, "C5 patch target not found exactly once - refusing to run"
    s = s.replace(needle,
        "self.loss_G = 0.0 * self.loss_G_GAN + self.loss_G_LPIPS   # C5: LPIPS-only arm")
    open(p, "w").write(s)
    print("[C5] adversarial term zeroed in the Kaggle copy of pix2pix_model.py", flush=True)

# ---------------------------------------------------------------------------------------
# Sharp half of the stop rule - the half that has never been able to fire.
#
# phase-c-config.md described it in words only ("a generator-loss spike in the first few
# hundred iterations, the actual cold-D signature"); corrections-log entry 5 gives a 20-row
# running-median baseline but no magnitude; and until this file there was NO implementation
# anywhere in the repository. Across two packages it was called the operative divergence
# test while nothing was watching. Recorded as corrections-log entry 28.
#
# CALIBRATED, not guessed, on the four completed seed-42 runs. Max ratio of a logged
# reconstruction-loss row to its own trailing 20-row running median, inside the window, taken
# over every stage the run has (the adversarial arms have two, and the check runs on each):
#     C1 1.5692   C2 1.5091   C4 1.1626   C5 1.0906     (highest per-run: 1.5692, C1 stage 2)
# Per stage: C1 warm-up 1.3806 / main 1.5692; C2 1.5091; C4 warm-up 1.1626 / main 1.1041;
# C5 1.0906. Highest anywhere in those four runs, outside the window included: 1.8792 (C2).
# Threshold 2.5 is 1.59x the highest windowed value and 1.33x the highest value seen anywhere
# in four runs that all finished normally. All six stage-windows were replayed through this
# exact code and produce zero hits. The margin is printed at run time so a reader sees it
# rather than trusting it.
#
# The quantity is the RECONSTRUCTION loss (G_L1, or G_LPIPS on the C4/C5 arms), not G_GAN,
# for a mechanistic reason and not a convenience one: the failure this gate exists to catch is
# cold-D damage to the GENERATOR, which shows up as degraded output quality, and the
# reconstruction loss measures output quality directly. G_GAN measures the state of the
# adversarial game - how well a discriminator initialised from noise is currently separating
# G's output - which is EXPECTED to swing hard early as D learns. That swing is the game
# equilibrating, not evidence of damage, so G_GAN is the wrong quantity for a damage detector
# regardless of its variance. Supporting evidence, not the argument: G_GAN in normal training
# reaches 3.75x on C1 and 2.85x on C4 against this same statistic, so a G_GAN detector at this
# threshold would also have false-fired on healthy runs.
#
# It is a NOVELTY detector, not a validated divergence test. It catches a run that looks
# unlike anything we have seen. It has never been shown to catch divergence, because
# divergence has never been observed here. Prospective only, like AMENDMENT C45-a.
SPIKE_MULT        = 2.5     # threshold, calibrated above
SPIKE_WINDOW_ROWS = 100     # first 500 optimizer steps = 2000 images = 100 rows at print_freq 10
SPIKE_MEDIAN_ROWS = 20      # trailing running-median window, inherited from entry 5
SPIKE_MIN_HITS    = 2       # two rows over threshold stop the run
_ROW = re.compile(r"\(epoch: (\d+), iters: (\d+)[^)]*\)(.*)")


def _spike_hits(vals):
    """Rows in the window whose ratio to the trailing 20-row median reaches the threshold."""
    v = vals[:SPIKE_WINDOW_ROWS]
    hits = []
    for i in range(SPIKE_MEDIAN_ROWS, len(v)):
        med = statistics.median(v[i - SPIKE_MEDIAN_ROWS:i])
        if med <= 0:
            continue
        r = v[i] / med
        if r >= SPIKE_MULT:
            hits.append((i, v[i], med, r))
    return hits


def run_train(cmd, env, stage):
    """Run one training stage, streaming its log, and evaluate the sharp half after epoch 1.

    The check runs at the END OF THE FIRST EPOCH of the stage - roughly ten minutes on the
    LPIPS arms - so the cost of watching is bounded and the rule can actually terminate a
    run. Every line the child prints is echoed unchanged, so the Kaggle log is exactly what
    it would have been without the monitor.
    """
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    vals, first_epoch, checked = [], None, False
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        m = _ROW.search(line)
        if not m:
            continue
        ep, tail = int(m.group(1)), m.group(3)
        if first_epoch is None:
            first_epoch = ep
        if ep == first_epoch and not checked:
            for key in ("G_LPIPS", "G_L1"):
                mm = re.search(key + r": ([\d.]+)", tail)
                if mm:
                    vals.append(float(mm.group(1)))
                    break
        elif ep > first_epoch and not checked:
            checked = True
            hits = _spike_hits(vals)
            obs = max((v / statistics.median(vals[i - SPIKE_MEDIAN_ROWS:i])
                       for i, v in enumerate(vals[:SPIKE_WINDOW_ROWS])
                       if i >= SPIKE_MEDIAN_ROWS
                       and statistics.median(vals[i - SPIKE_MEDIAN_ROWS:i]) > 0),
                      default=float("nan"))
            print(f"\n[stop-rule/sharp] {ARM} seed {SEED} stage {stage}: evaluated after epoch "
                  f"{first_epoch} on {min(len(vals), SPIKE_WINDOW_ROWS)} rows. "
                  f"max ratio observed {obs:.4f}; threshold {SPIKE_MULT} "
                  f"(seed-42 calibration: max windowed 1.5692, max anywhere 1.8792); "
                  f"hits {len(hits)}/{SPIKE_MIN_HITS} needed.", flush=True)
            if len(hits) >= SPIKE_MIN_HITS:
                print(f"[stop-rule/sharp] FIRED - terminating {ARM} seed {SEED}. "
                      f"Report this, whatever it costs the package "
                      f"(seed-replication-registration.md, Stop rule).", flush=True)
                for i, v, med, r in hits:
                    print(f"    row {i}: value {v:.4f}, trailing median {med:.4f}, "
                          f"ratio {r:.3f}", flush=True)
                proc.terminate()
                try:
                    proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    proc.kill()
                sys.exit(3)
    rc = proc.wait()
    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)


base = [sys.executable, f"{ROOT}/train.py",
        "--dataroot", f"{ROOT}/datasets/tr", "--name", ARM,
        "--model","pix2pix","--direction","BtoA","--netG","unet_256","--norm","batch",
        "--load_size","286","--crop_size","256","--batch_size","4",
        "--checkpoints_dir","/kaggle/working/checkpoints",
        "--continue_train","--epoch","latest",
        "--save_epoch_freq","1","--display_id","-1","--print_freq","10"]
if ARM in ("C4", "C5"):
    # Reconstruction term = LPIPS instead of L1, by the repository's own stock flag:
    # pix2pix_model.py replaces criterionL1 with LearnedPerceptualImagePatchSimilarity
    # (net_type='vgg'), weighted by the same lambda_L1 (default 100). This is the
    # published HR objective per the paper's Table 5 (Adversarial + lambda*LPIPS);
    # see phase-c-lpips-registration.md, Gate 0.
    base += ["--LPIPS"]
if ARM in ("C1", "C4"):   # stage 1: low-LR joint warm-up (D catches up, G barely moves)
    banner(PROVENANCE)
    # --lr_policy step --lr_decay_iters 50: hold 2e-5 CONSTANT across both warm-up epochs.
    # The default 'linear' policy steps its lambda at the START of each epoch and with
    # n_epochs_decay=0 the denominator is 1, so warm-up epoch 2 ran at lr = 0 exactly - half
    # the registered warm-up was dead. StepLR(step_size=50) cannot trigger inside a 2-epoch
    # stage. Stock CLI flags only; stage 2 and C2 keep the default linear policy untouched.
    # Registered as a dated amendment in phase-c-config.md before any C1 result existed.
    run_train(base+["--lr","2e-5","--n_epochs","2","--n_epochs_decay","0",
                    "--epoch_count","1","--lr_policy","step","--lr_decay_iters","50"],
              ENV, "1 (warm-up)")
    banner(PROVENANCE)
    run_train(base+["--lr","1e-4","--n_epochs","10","--n_epochs_decay","10",
                    "--epoch_count","3"], ENV, "2 (main)")
else:               # C2/C3/C5: no adversarial gradient -> no warm-up needed.
                    # C3 deliberately reuses C2's EXACT invocation (linear 10+10 schedule).
                    # A work-package instruction had also said "same lr_policy step /
                    # lr_decay_iters 50"; the author confirmed on 20 Aug 2026 that this was
                    # their error (the flag belonged to the discarded C1 warm-up run).
                    # Controlled arm: nothing changes except the data mix.
    banner(PROVENANCE)
    run_train(base+["--lr","1e-4","--n_epochs","10","--n_epochs_decay","10",
                    "--epoch_count","1"], ENV, "1 (single)")
print(f"{ARM} done; checkpoints in /kaggle/working/checkpoints/{ARM}")
