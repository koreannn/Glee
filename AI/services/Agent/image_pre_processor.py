from io import BytesIO

from PIL import ImageOps
from PIL.Image import Image
from loguru import logger


class ImagePreprocessor:
    def preprocess(self, image_bytes: bytes) -> bytes:
        """이미지 전처리를 수행합니다."""
        try:
            # 이미지 로드 및 전처리
            image = Image.open(BytesIO(image_bytes))

            # 이미지 정규화 (크기 조정, 회전 등)
            image = ImageOps.exif_transpose(image)  # EXIF 정보에 따라 이미지 회전

            # 결과 이미지를 바이트로 변환
            output_buffer = BytesIO()
            image.save(output_buffer, format=image.format or "PNG")
            return output_buffer.getvalue()
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_bytes
