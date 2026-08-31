from locust import HttpUser, task, between
import io
from PIL import Image

class PlantDiseaseAPIUser(HttpUser):
    # Simulate a user waiting between 0.5 to 1.5 seconds between tasks
    wait_time = between(0.5, 1.5)

    def on_start(self):
        # Create a mock image in-memory for load testing
        img = Image.new("RGB", (224, 224), color="green")
        self.image_bytes = io.BytesIO()
        img.save(self.image_bytes, format="JPEG")
        self.image_bytes.seek(0)

    @task(3)
    def test_predict_endpoint(self):
        # Send POST request to prediction endpoint with file
        self.image_bytes.seek(0)
        files = {
            "file": ("test_leaf.jpg", self.image_bytes, "image/jpeg")
        }
        with self.client.post("/api/predict", files=files, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # 429 is Too Many Requests (SlowAPI rate limit hit)
                # Under load, hitting the rate limiter is expected and means it's working!
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def test_health_endpoint(self):
        # Send GET request to health endpoint
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
