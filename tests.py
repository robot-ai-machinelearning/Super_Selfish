from super_selfish.models import CombinedNet, Classification, ReshapeChannels, EfficientFeatures
from super_selfish.efficientnet_pytorch.model import EfficientNet
import torchvision.datasets as datasets
from super_selfish.supervisors import LabelSupervisor, RotateNetSupervisor, ExemplarNetSupervisor, \
    JigsawNetSupervisor, DenoiseNetSupervisor, ContextNetSupervisor, BiGanSupervisor, \
    SplitBrainNetSupervisor, ContrastivePredictiveCodingSupervisor, MomentumContrastSupervisor, \
    BYOLSupervisor, InstanceDiscriminationSupervisor, ContrastiveMultiviewCodingSupervisor, \
    PIRLSupervisor
from torchvision import transforms
from torch import nn
import torch
from torch.utils.data import random_split
from super_selfish.utils import test
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Configuration
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Choose supervisor
supervisor_name = 'momentum'
lr = 1e-3
epochs = 1
batch_size = 48
device = 'cuda'

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Data
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Start off with CIFAR
train_dataset, val_dataset = random_split(datasets.CIFAR10(root='./datasets/', train=True,
                                                           download=False,
                                                           transform=transforms.Compose([transforms.Resize((225, 225)), transforms.ToTensor()])),
                                          [45000, 5000],
                                          generator=torch.Generator().manual_seed(42))
test_dataset = datasets.CIFAR10(root='./datasets/', train=False,
                                download=False, transform=transforms.Compose([transforms.Resize((225, 225)), transforms.ToTensor()]))

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Self Supervision
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Create supervisor
if supervisor_name == 'rotate':
    supervisor = RotateNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'exemplar':
    supervisor = ExemplarNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'jigsaw':
    supervisor = JigsawNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'denoise':
    supervisor = DenoiseNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'context':
    supervisor = ContextNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'bi':
    supervisor = BiGanSupervisor(train_dataset).to(device)
elif supervisor_name == 'splitbrain':
    supervisor = SplitBrainNetSupervisor(train_dataset).to(device)
elif supervisor_name == 'coding':
    supervisor = ContrastivePredictiveCodingSupervisor(
        train_dataset).to(device)
elif supervisor_name == 'momentum':
    supervisor = MomentumContrastSupervisor(train_dataset).to(device)
elif supervisor_name == 'byol':
    supervisor = BYOLSupervisor(train_dataset).to(device)
elif supervisor_name == 'discrimination':
    supervisor = InstanceDiscriminationSupervisor(train_dataset).to(device)
elif supervisor_name == 'multiview':
    supervisor = ContrastiveMultiviewCodingSupervisor(train_dataset).to(device)
elif supervisor_name == 'pirl':
    supervisor = PIRLSupervisor(train_dataset).to(device)

# Start training
supervisor.supervise(lr=lr, epochs=epochs,
                     batch_size=batch_size, name="store/base_" + supervisor_name, pretrained=False)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Finetune with self supervised features
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Finetune on "right" target with less epochs and lower lr
epochs = 1
lr = 1e-3
backbone = supervisor.get_backbone()
predictor = Classification([3136, 1024, 256, 10])
combined = CombinedNet(backbone, predictor).to(device)

# Label supervisor without self-supervision and only backprob through mlp
supervisor = LabelSupervisor(combined, val_dataset)
# Start training
supervisor.supervise(lr=lr, epochs=epochs,
                     batch_size=batch_size, name="store/finetuned_" + supervisor_name, pretrained=False)
test(combined, test_dataset)
