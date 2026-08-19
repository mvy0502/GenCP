# Kaggle notebook script — Phase C arms C1 (GAN+L1) and C2 (L1-only)
# Dataset "gencp-tr" mounted at /kaggle/input/gencp-tr
# Full rationale: tubitak/docs/phase-c-config.md ; registration: phase-c-registration.md
import os, subprocess, shutil, sys
ARM = os.environ.get("ARM", "C1")            # set "C2" for the L1-only arm
ROOT = "/kaggle/working/GenCP"
DATA = "/kaggle/input/gencp-tr"

subprocess.run(["git","clone","--depth","1","-b","tubitak-tr",
                "https://github.com/mvy0502/GenCP.git", ROOT], check=True)
subprocess.run([sys.executable,"-m","pip","install","-q","dominate","visdom"], check=False)

os.makedirs(f"{ROOT}/datasets/tr/train", exist_ok=True)
for f in os.listdir(f"{DATA}/pairs/train"):
    os.symlink(f"{DATA}/pairs/train/{f}", f"{ROOT}/datasets/tr/train/{f}")
ck = f"/kaggle/working/checkpoints/{ARM}"     # persistent output
os.makedirs(ck, exist_ok=True)
shutil.copy(f"{DATA}/latest_net_G.pth", f"{ck}/latest_net_G.pth")

if ARM == "C2":                               # L1-only: zero the GAN term (Kaggle copy only)
    p = f"{ROOT}/models/pix2pix_model.py"
    s = open(p).read().replace(
        "self.loss_G = self.loss_G_GAN + self.loss_G_L1",
        "self.loss_G = 0.0 * self.loss_G_GAN + self.loss_G_L1   # C2: L1-only arm")
    open(p, "w").write(s)

base = [sys.executable, f"{ROOT}/train.py",
        "--dataroot", f"{ROOT}/datasets/tr", "--name", ARM,
        "--model","pix2pix","--direction","BtoA","--netG","unet_256","--norm","batch",
        "--load_size","286","--crop_size","256","--batch_size","4",
        "--checkpoints_dir","/kaggle/working/checkpoints",
        "--continue_train","--epoch","latest",
        "--save_epoch_freq","1","--display_id","-1","--seed","42"]
if ARM == "C1":     # stage 1: low-LR joint warm-up (D catches up, G barely moves)
    subprocess.run(base+["--lr","2e-5","--n_epochs","2","--n_epochs_decay","0",
                         "--epoch_count","1"], check=True)
    subprocess.run(base+["--lr","1e-4","--n_epochs","10","--n_epochs_decay","10",
                         "--epoch_count","3"], check=True)
else:               # C2: no adversarial gradient -> no warm-up needed
    subprocess.run(base+["--lr","1e-4","--n_epochs","10","--n_epochs_decay","10",
                         "--epoch_count","1"], check=True)
print(f"{ARM} done; checkpoints in /kaggle/working/checkpoints/{ARM}")
