import os

import numpy as np
import torch
from data.base_dataset import BaseDataset, get_transform
from data.image_folder import make_dataset
from PIL import Image


class TopoSingleDataset(BaseDataset):
    """
    Pix2Pix TOPO Dataset where input A = RGB + TOPO (4 canaux)
    """

    def __init__(self, opt):
        BaseDataset.__init__(self, opt)

        self.dir_A_rgb = os.path.join(opt.dataroot, 'A')
        self.dir_A_topo = os.path.join(opt.dataroot, 'TOPO')

        self.A_rgb_paths = sorted(make_dataset(self.dir_A_rgb, opt.max_dataset_size))
        self.A_topo_paths = sorted(make_dataset(self.dir_A_topo, opt.max_dataset_size))

        # Check if folders have the same length
        assert len(self.A_rgb_paths) == len(self.A_topo_paths), \
            f"Folders should have the same length" \
            f"A: {len(self.A_rgb_paths)}, TOPO: {len(self.A_topo_paths)}"

        # Check file's names consistency
        for i in range(len(self.A_rgb_paths)):
            a_name = os.path.basename(self.A_rgb_paths[i])
            topo_name = os.path.basename(self.A_topo_paths[i])
            
            a_base = os.path.splitext(a_name)[0]
            topo_base = os.path.splitext(topo_name)[0]
            
            if a_base != topo_base :
                raise ValueError(
                    f"Files not matching index {i}:\n"
                    f"  A: {a_name}\n"
                    f"  TOPO: {topo_name}\n"
                )

        self.transform_A_rgb = get_transform(opt, grayscale=False)
        self.transform_A_topo = get_transform(opt, grayscale=True)

    def __getitem__(self, index):
        A_rgb_path = self.A_rgb_paths[index]
        A_topo_path = self.A_topo_paths[index]
        
        A_rgb = Image.open(A_rgb_path).convert('RGB')
        A_topo = Image.open(A_topo_path).convert('L')  # grayscale conversion for TOPO files

        A_rgb_tensor = self.transform_A_rgb(A_rgb)  # [3, H, W]
        A_topo_tensor = self.transform_A_topo(A_topo)  # [1, H, W]

        # Concatenate tensors
        A = torch.cat([A_rgb_tensor, A_topo_tensor], dim=0)  # [4, H, W]

        return {
            'A': A, 
            'A_paths': A_rgb_path,
        }

    def __len__(self):
        return len(self.A_rgb_paths)
