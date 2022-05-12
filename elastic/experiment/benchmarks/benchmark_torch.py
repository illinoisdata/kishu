#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Adapted from https://colab.research.google.com/drive/1gCgtlnMPVWY0l1ra8ssS0EzJiWaVR4Pk

from core.event import operation_events
from core.graph.graph import DependencyGraph
from core.graph.search import find_path
from core.io.external_storage import ExternalStorage
from core.io.filesystem_adapter import FilesystemAdapter
from core.record_event import RecordEvent
from algorithm.baseline import MigrateAllBaseline
from experiment.migrate import migrate

########## BEGIN BENCHMARK CODE

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms


@RecordEvent
def cell_2():
    print(torch.__version__)

@RecordEvent
def cell_3():
    BATCH_SIZE = 32

    ## transformations
    transform = transforms.Compose(
        [transforms.ToTensor()])

    ## download and load training dataset
    trainset = torchvision.datasets.MNIST(root='./data', train=True,
                                            download=True, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE,
                                            shuffle=True, num_workers=2)

    ## download and load testing dataset
    testset = torchvision.datasets.MNIST(root='./data', train=False,
                                        download=True, transform=transform)
    testloader = torch.utils.data.DataLoader(testset, batch_size=BATCH_SIZE,
                                            shuffle=False, num_workers=2)
    
    return BATCH_SIZE, transform, trainset, trainloader, testset, testloader

@RecordEvent
def cell_4(trainloader):
    import matplotlib.pyplot as plt
    import numpy as np

    ## functions to show an image
    def imshow(img):
        #img = img / 2 + 0.5     # unnormalize
        npimg = img.numpy()
        plt.imshow(np.transpose(npimg, (1, 2, 0)))

    ## get some random training images
    dataiter = iter(trainloader)
    images, labels = dataiter.next()

    ## show images
    imshow(torchvision.utils.make_grid(images))
    
    return dataiter, images, labels

@RecordEvent
def cell_5(trainloader):
    for images, labels in trainloader:
        print("Image batch dimensions:", images.shape)
        print("Image label dimensions:", labels.shape)
        break
    
class MyModel(nn.Module):
    def __init__(self):
        super(MyModel, self).__init__()

        # 28x28x1 => 26x26x32
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3)
        self.d1 = nn.Linear(26 * 26 * 32, 128)
        self.d2 = nn.Linear(128, 10)

    def forward(self, x):
        # 32x1x28x28 => 32x32x26x26
        x = self.conv1(x)
        x = F.relu(x)

        # flatten => 32 x (32*26*26)
        x = x.flatten(start_dim = 1)

        # 32 x (32*26*26) => 32x128
        x = self.d1(x)
        x = F.relu(x)

        # logits => 32x10
        logits = self.d2(x)
        out = F.softmax(logits, dim=1)
        return out
    
@RecordEvent
def cell_6(trainloader):
    ## test the model with 1 batch
    model = MyModel()
    for images, labels in trainloader:
        print("batch size:", images.shape)
        out = model(images)
        print(out.shape)
        break
    return model, out

@RecordEvent
def cell_7():
    learning_rate = 0.001
    num_epochs = 5

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = MyModel()
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    return learning_rate, num_epochs, device, model, criterion, optimizer

## compute accuracy
def get_accuracy(logit, target, batch_size):
    ''' Obtain accuracy for training round '''
    corrects = (torch.max(logit, 1)[1].view(target.size()).data == target.data).sum()
    accuracy = 100.0 * corrects/batch_size
    return accuracy.item()

@RecordEvent
def cell_9(model, num_epochs, trainloader, device, criterion, optimizer, BATCH_SIZE):
    for epoch in range(num_epochs):
        train_running_loss = 0.0
        train_acc = 0.0

        model = model.train()

        ## training step
        for i, (images, labels) in enumerate(trainloader):
            
            images = images.to(device)
            labels = labels.to(device)

            ## forward + backprop + loss
            logits = model(images)
            loss = criterion(logits, labels)
            optimizer.zero_grad()
            loss.backward()

            ## update model params
            optimizer.step()

            train_running_loss += loss.detach().item()
            train_acc += get_accuracy(logits, labels, BATCH_SIZE)
        
        model.eval()
        print('Epoch: %d | Loss: %.4f | Train Accuracy: %.2f' \
            %(epoch, train_running_loss / i, train_acc/i))
    return epoch, train_running_loss, train_acc, model, images, labels, logits, loss

@RecordEvent
def cell_10(testloader, device, model, BATCH_SIZE):
    test_acc = 0.0
    for i, (images, labels) in enumerate(testloader, 0):
        images = images.to(device)
        labels = labels.to(device)
        outputs = model(images)
        test_acc += get_accuracy(outputs, labels, BATCH_SIZE)
            
    print('Test Accuracy: %.2f'%( test_acc/i))
    return test_acc, i, images, labels, outputs

def main():
    ########## BEGIN BENCHMARK
    cell_2()
    BATCH_SIZE, transform, trainset, trainloader, testset, testloader = cell_3()
    dataiter, images, labels = cell_4(trainloader)
    cell_5(trainloader)
    model, out = cell_6(trainloader)
    learning_rate, num_epochs, device, model, criterion, optimizer = cell_7()
    epoch, train_running_loss, train_acc, model, images, labels, logits, loss = cell_9(model, num_epochs, trainloader, device, criterion, optimizer, BATCH_SIZE)
    test_acc, i, images, labels, outputs = cell_10(testloader, device, model, BATCH_SIZE)
    ########## END BENCHMARK
    
    ########## BEGIN MIGRATION
    graph = DependencyGraph()
    selector = MigrateAllBaseline(graph, graph.active_nodes.values())
    nodes_to_migrate = selector.select_nodes()
    locs = locals()
    objects_to_migrate = [locs[node.var.name] for node in nodes_to_migrate]
    recomp_path = find_path(graph, nodes_to_migrate, operation_events)
    storage = ExternalStorage()
    storage.register("local", FilesystemAdapter())
    glbs, locs = globals(), locals()
    context_items = {**glbs, **locs}.items()
    migrate(objects_to_migrate, recomp_path, storage, context_items)
    ########## END MIGRATION

if __name__ == '__main__':
    main()
