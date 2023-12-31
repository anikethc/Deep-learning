

import time
from torchvision import datasets
from torchvision import transforms
from torch.utils.data import DataLoader
import torch.nn.functional as F
import torch
import numpy as np
import os
import matplotlib.pyplot as plt

"""## Settings and Dataset"""

##########################
### SETTINGS
##########################

# Device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Hyperparameters
random_seed = 123
learning_rate = 0.1
num_epochs = 200
batch_size = 5

# Architecture
num_features = 784
num_classes = 10
num_hidden1=50
num_hidden2=20

##########################
### MNIST DATASET
##########################

train_dataset = datasets.MNIST(root='data',
                               train=True,
                               transform=transforms.ToTensor(),
                               download=True)
trainset= torch.utils.data.Subset(train_dataset,range(20))
validationset= torch.utils.data.Subset(train_dataset,range(20,len(train_dataset)))
# test_dataset = datasets.MNIST(root='data',
#                               train=False,
#                               transform=transforms.ToTensor())


train_loader = DataLoader(dataset=trainset,
                          batch_size=batch_size,
                          shuffle=True)
validation_loader = DataLoader(dataset=validationset,
                          batch_size=batch_size,
                          shuffle=True)
# test_loader = DataLoader(dataset=test_dataset,
#                          batch_size=batch_size,
#                          shuffle=False)


# Checking the dataset
for images, labels in train_loader:
    print('Image batch dimensions:', images.shape) #NCHW
    print('Image label dimensions:', labels.shape)
    break

##########################
### MODEL
##########################

class MLP(torch.nn.Module):

    def __init__(self, num_features,num_hidden1,num_hidden2, num_classes):
        super().__init__()

        self.num_classes = num_classes
        self.num_hidden1=num_hidden1,
        self.num_hidden2=num_hidden2,
        self.model = torch.nn.Sequential(
        torch.nn.Flatten(),
        torch.nn.Linear(num_features, num_hidden1),
        torch.nn.ReLU(),
        torch.nn.Linear(num_hidden1, num_hidden2),
        torch.nn.ReLU(),
        torch.nn.Linear(num_hidden2, num_classes))

    def forward(self, x):
        return self.model(x)

model = MLP(num_features=28*28,
            num_hidden1=num_hidden1,
            num_hidden2=num_hidden2,
            num_classes=num_classes)

model.to(device)

##########################
### COST AND OPTIMIZER
##########################

optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

# Manual seed for deterministic data loader
torch.manual_seed(random_seed)

def compute_accuracy(model, data_loader, device):

    with torch.no_grad():

        correct_pred, num_examples = 0, 0

        for i, (features, targets) in enumerate(data_loader):

            features = features.to(device)
            targets = targets.float().to(device)

            logits = model(features)
            _, predicted_labels = torch.max(logits, 1)

            num_examples += targets.size(0)
            correct_pred += (predicted_labels == targets).sum()
    return correct_pred.float()/num_examples * 100

def train_model(model, num_epochs, train_loader,
                valid_loader, optimizer, device):

    start_time = time.time()
    minibatch_loss_list, train_acc_list, valid_acc_list = [], [], []
    for epoch in range(num_epochs):

        model.train()
        for batch_idx, (features, targets) in enumerate(train_loader):
            # print(batch_idx)
            features = features.to(device)
            targets = targets.to(device)

            # ## FORWARD AND BACK PROP
            logits = model(features)
            loss = torch.nn.functional.cross_entropy(logits, targets)
            optimizer.zero_grad()

            loss.backward()

            # ## UPDATE MODEL PARAMETERS
            optimizer.step()

            # ## LOGGING
            minibatch_loss_list.append(loss.item())
            if not batch_idx % 50:
                print(f'Epoch: {epoch+1:03d}/{num_epochs:03d} '
                      f'| Batch {batch_idx:04d}/{len(train_loader):04d} '
                      f'| Loss: {loss:.4f}')

        model.eval()
        with torch.no_grad():  # save memory during inference
            train_acc = compute_accuracy(model, train_loader, device=device)
            valid_acc = compute_accuracy(model, valid_loader, device=device)
            print(f'Epoch: {epoch+1:03d}/{num_epochs:03d} '
                  f'| Train: {train_acc :.2f}% '
                  f'| Validation: {valid_acc :.2f}%')
            train_acc_list.append(train_acc.item())
            valid_acc_list.append(valid_acc.item())

        elapsed = (time.time() - start_time)/60
        print(f'Time elapsed: {elapsed:.2f} min')

    elapsed = (time.time() - start_time)/60
    print(f'Total Training Time: {elapsed:.2f} min')

    # test_acc = compute_accuracy(model, test_loader, device=device)
    # print(f'Test accuracy {test_acc :.2f}%')

    return minibatch_loss_list, train_acc_list, valid_acc_list




# start_time = time.time()
# epoch_costs = []
# for epoch in range(num_epochs):
#     avg_cost = 0.
#     for batch_idx, (features, targets) in enumerate(train_loader):

#         features = features.view(-1, 28*28).to(device)
#         targets = targets.to(device)

#         ### FORWARD AND BACK PROP
#         print(model(features))
#         logits, probas = model(features)

#         # note that the PyTorch implementation of
#         # CrossEntropyLoss works with logits, not
#         # probabilities
#         cost = F.cross_entropy(logits, targets)
#         optimizer.zero_grad()
#         cost.backward()
#         avg_cost += cost

#         ### UPDATE MODEL PARAMETERS
#         optimizer.step()

#         ### LOGGING
#         if not batch_idx % 50:
#             print ('Epoch: %03d/%03d | Batch %03d/%03d | Cost: %.4f'
#                    %(epoch+1, num_epochs, batch_idx,
#                      len(train_dataset)//batch_size, cost))

#     with torch.set_grad_enabled(False):
#         avg_cost = avg_cost/len(train_dataset)
#         epoch_costs.append(avg_cost)
#         print('Epoch: %03d/%03d training accuracy: %.2f%%' % (
#               epoch+1, num_epochs,
#               compute_accuracy(model, train_loader)))
#         print('Time elapsed: %.2f min' % ((time.time() - start_time)/60))

minibatch_loss_list, train_acc_list, valid_acc_list = train_model(
    model=model,
    num_epochs=num_epochs,
    train_loader=train_loader,
    valid_loader=validation_loader,
    optimizer=optimizer,
    device=device)

def plot_training_loss(minibatch_loss_list, num_epochs, iter_per_epoch,
                       results_dir=None, averaging_iterations=100):

    plt.figure()
    ax1 = plt.subplot(1, 1, 1)
    ax1.plot(range(len(minibatch_loss_list)),
             (minibatch_loss_list), label='Minibatch Loss')

    if len(minibatch_loss_list) > 1000:
        ax1.set_ylim([
            0, np.max(minibatch_loss_list[1000:])*1.5
            ])
    ax1.set_xlabel('Iterations')
    ax1.set_ylabel('Loss')

    ax1.plot(np.convolve(minibatch_loss_list,
                         np.ones(averaging_iterations,)/averaging_iterations,
                         mode='valid'),
             label='Running Average')
    ax1.legend()

    ###################
    # Set scond x-axis
    ax2 = ax1.twiny()
    newlabel = list(range(num_epochs+1))

    newpos = [e*iter_per_epoch for e in newlabel]

    ax2.set_xticks(newpos[::10])
    ax2.set_xticklabels(newlabel[::10])

    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 45))
    ax2.set_xlabel('Epochs')
    ax2.set_xlim(ax1.get_xlim())
    ###################

    plt.tight_layout()

    if results_dir is not None:
        image_path = os.path.join(results_dir, 'plot_training_loss.pdf')
        plt.savefig(image_path)


def plot_accuracy(train_acc_list, valid_acc_list, results_dir):

    num_epochs = len(train_acc_list)

    plt.plot(np.arange(1, num_epochs+1),
             train_acc_list, label='Training')
    plt.plot(np.arange(1, num_epochs+1),
             valid_acc_list, label='Validation')

    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()

    plt.tight_layout()

    if results_dir is not None:
        image_path = os.path.join(
            results_dir, 'plot_acc_training_validation.pdf')
        plt.savefig(image_path)

# plot_training_loss(minibatch_loss_list=minibatch_loss_list,
#                    num_epochs=num_epochs,
#                    iter_per_epoch=len(train_loader),
#                    results_dir=None,
#                    averaging_iterations=20)
# plt.show()

plot_accuracy(train_acc_list=train_acc_list,
              valid_acc_list=valid_acc_list,
              results_dir=None)
plt.show()