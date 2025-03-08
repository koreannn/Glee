from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from loguru import logger


class ImagePreprocessor:
    def preprocess(self, image_bytes: bytes, output_format: str = "PNG") -> bytes:
        """이미지 전처리를 수행하고 메모리에서 직접 변환합니다."""
        try:
            # 이미지 로드
            with BytesIO(image_bytes) as input_buffer:
                with Image.open(input_buffer) as image:
                    # EXIF 정보에 따른 자동 회전
                    image = ImageOps.exif_transpose(image)

                    # 출력 버퍼 생성 및 저장
                    with BytesIO() as output_buffer:
                        image.save(output_buffer, format=image.format or output_format)
                        return output_buffer.getvalue()

        except UnidentifiedImageError as e:
            logger.error(f"[ImagePreprocessor] 올바르지 않은 이미지 데이터: {e}")
            raise ValueError("올바르지 않은 이미지 데이터입니다.")

        except KeyError as e:
            logger.error(f"[ImagePreprocessor] 지원되지 않는 이미지 포맷: {output_format}, 오류: {e}")
            raise ValueError(f"지원되지 않는 이미지 포맷입니다: {output_format}")

        except MemoryError as e:
            logger.critical("[ImagePreprocessor] 메모리 부족 오류 발생!")
            raise ValueError("이미지가 너무 커서 메모리 부족 오류가 발생했습니다.")

        except Exception as e:
            logger.exception(f"[ImagePreprocessor] 이미지 전처리 중 예상치 못한 오류 발생: {e}")
            raise RuntimeError(f"이미지 전처리 중 예상치 못한 오류 발생: {e}")
