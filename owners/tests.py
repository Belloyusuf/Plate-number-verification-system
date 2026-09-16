import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .alpr import ALPRService
from .models import CarRegisteration, Owner


class ALPRServiceTests(TestCase):
    def test_process_upload_returns_plate_prediction_for_selected_model(self):
        image_bytes = io.BytesIO()
        Image.new("RGB", (160, 90), color=(255, 255, 255)).save(image_bytes, format="PNG")
        uploaded_file = SimpleUploadedFile(
            "sample_plate.png",
            image_bytes.getvalue(),
            content_type="image/png",
        )

        result = ALPRService.process_upload(uploaded_file, "YOLOv8")

        self.assertEqual(result["model_name"], "YOLOv8")
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertIn(result["status"], {"fallback", "ocr-detected", "registered", "not-found"})

    def test_process_upload_checks_registered_plate_against_database(self):
        owner = Owner.objects.create(
            full_name="Ada Okafor",
            sex="Female",
            marital_status="Married",
            occupation="Civil Servant",
            date_of_birth="1990-01-01",
            phone="08012345678",
            email="ada@example.com",
            residential_address="Lagos",
            state="Lagos",
            local_government="Ikeja",
            nationality="Nigerian",
        )
        CarRegisteration.objects.create(
            owner=owner,
            vehicle_category="Private",
            vehicle_sub_category="State Ministries/Agencies/Department",
            old_plate_number="ABC123",
            vehicle_make="Toyota",
            color="Silver",
            fuel_type="Petrol",
            year_of_manufacture="2020",
            model="Camry",
            engine_number="ENG001",
            policy_number="POL001",
            vehicle_type="Toyota",
            chassis_no="CH001",
            engine_capacity="Between 2.1 and 3.0",
            tank_capacity="60",
            odometer="12000",
        )

        image_bytes = io.BytesIO()
        Image.new("RGB", (160, 90), color=(255, 255, 255)).save(image_bytes, format="PNG")
        uploaded_file = SimpleUploadedFile(
            "ABC123.png",
            image_bytes.getvalue(),
            content_type="image/png",
        )

        result = ALPRService.process_upload(uploaded_file, "YOLOv8")

        self.assertTrue(result["record_found"])
        self.assertEqual(result["plate_number"], "ABC123")
        self.assertEqual(result["vehicle_owner"], "Ada Okafor")
        self.assertEqual(result["vehicle_type"], "Toyota")
        self.assertEqual(result["status"], "registered")
