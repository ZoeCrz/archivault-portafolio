from django.test import SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .validators import validate_image_file
from .test_images import PNG_BYTES

class UploadValidationTests(SimpleTestCase):
    def test_valid_image_and_stream_position(self):
        image = SimpleUploadedFile('a.png', PNG_BYTES, content_type='image/png')
        validate_image_file(image)
        self.assertEqual(image.tell(), 0)

    def test_spoofed_image_rejected(self):
        with self.assertRaises(ValidationError):
            validate_image_file(SimpleUploadedFile('a.png', b'<script>alert(1)</script>', content_type='image/png'))
