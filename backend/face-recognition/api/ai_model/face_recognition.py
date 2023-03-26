from facenet_pytorch import MTCNN, InceptionResnetV1, fixed_image_standardization, training
import torch
from torchvision import datasets, transforms
import numpy as np
import os
import cv2
from PIL import Image
import hnswlib


class FaceRecognition():
    def __init__(self, gpu=False):
        self.device = torch.device(
            'cuda:0' if torch.cuda.is_available() and gpu else 'cpu')
        self.mtcnn = MTCNN(
            thresholds=[0.7, 0.7, 0.8], keep_all=True, device=self.device)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
        self.p = None
        self.names = None

    def trans_for_train(self, img):
        trans = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.2, hue=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        return trans(img).unsqueeze(0)

    def trans_for_recognition(self, img):
        trans = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        return trans(img).unsqueeze(0)

    def train(self, url):
        vicap = cv2.VideoCapture(url)
        success = True
        count = 0
        embs = []
        while success:
            success, image = vicap.read()
            count += 1
            if image is None:
                continue
            image = image[:, :, ::-1]
            if count % 5 == 0:
                count = 0
                boxes, _ = self.mtcnn.detect(image)
                if boxes is None:
                    continue
                box = boxes[0]
                bbox = list(map(int, box.tolist()))
                if min(bbox) < 0:
                    continue
                image = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                im_pil = Image.fromarray(image)
                face = self.trans_for_train(im_pil)
                with torch.no_grad():
                    emb = self.resnet(face)
                    emb = emb.detach()
                    if emb == []:
                        continue
                    embs.append(emb.numpy()[0].tolist())
        vicap.release()
        return embs

    def reload_hnswlib(self, embs, names):
        lg = len(names)
        p = hnswlib.Index(space='l2', dim=512)
        p.init_index(max_elements=lg, ef_construction=200, M=16)
        p.add_items(embs, np.arange(0, lg))
        p.save_index('data_file/embedding.bin')
        torch.save([names], 'data_file/names.pt')
        # self.p = None

    def predict(self, image):
        # if self.p == None:
        self.p = hnswlib.Index(space='l2', dim=512)
        saved_data = torch.load('data_file/names.pt')
        self.names = saved_data[0]
        self.p.load_index('data_file/embedding.bin', max_elements=len(self.names))
        # img = cv2.imread(image)
        
        img = image
        img = img[:,:,::-1]
        boxes, _ = self.mtcnn.detect(img)
        results = []
        if boxes is not None:
            for box in boxes:
                bbox = list(map(int, box.tolist()))
                img_region = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                im_pil = Image.fromarray(img_region)
                face = self.trans_for_recognition(im_pil)
                emb = self.resnet(face).detach()
                labels, distances = self.p.knn_query(emb, k=1)
                distance = distances[0][0]
                recognized = 'unknown'
                if distance < 0.6:
                    print(distance)
                    recognized = self.names[labels[0][0]]
                    results.append({'username': recognized,'distance': float(distance), 'coordinate': bbox})
                results.append(float(distance))
        return results