from ultralytics import RTDETR

model = RTDETR('rt-detr.pt')

model.info()

results = model("example.mp4", show=True, save=True, conf=0.6, iou=0.4, augment=True)