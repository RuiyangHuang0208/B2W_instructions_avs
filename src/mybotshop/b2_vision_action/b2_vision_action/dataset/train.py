from ultralytics import YOLO

# Load a model
model = YOLO("yolo11s.pt") 

# Train using the single most idle GPU
results = model.train(data="data.yaml", epochs=200, imgsz=640, device=0)