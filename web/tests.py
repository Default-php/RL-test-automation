from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from web.services import DatasetValidationError, load_uploaded_dataset, validate_dataset


class DatasetValidationTests(SimpleTestCase):
    def test_valid_dataset_is_converted_to_test_cases(self):
        dataset = [
            {
                "id": 1,
                "name": "Login test",
                "estimated_time": 1.2,
                "failure_probability": 0.25,
                "coverage_gain": 0.14,
                "priority": 5,
            }
        ]

        test_cases = validate_dataset(dataset)

        self.assertEqual(len(test_cases), 1)
        self.assertEqual(test_cases[0].name, "Login test")

    def test_missing_required_field_is_rejected(self):
        dataset = [
            {
                "id": 1,
                "name": "Login test",
                "estimated_time": 1.2,
                "coverage_gain": 0.14,
            }
        ]

        with self.assertRaises(DatasetValidationError):
            validate_dataset(dataset)

    def test_uploaded_json_file_is_loaded(self):
        uploaded = SimpleUploadedFile(
            "dataset.json",
            b'[{"id": 1, "name": "Login", "estimated_time": 1.0, '
            b'"failure_probability": 0.2, "coverage_gain": 0.1}]',
            content_type="application/json",
        )

        test_cases, dataset_name = load_uploaded_dataset(uploaded)

        self.assertEqual(dataset_name, "dataset.json")
        self.assertEqual(test_cases[0].id, 1)
