import re
import os
import sys

from typing import Any, Dict, List, Optional, Tuple

from django.core.files.uploadedfile import UploadedFile
from PIL import Image

from .models import CarRegisteration

# Set Tesseract path for Windows; on Linux the binary is found via PATH automatically
if sys.platform == "win32":
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except ImportError:
        pass


# ── Nigerian state data ────────────────────────────────────────────────────────
# Maps state name keywords → (full state name, slogan)
NIGERIAN_STATES = {
    "LAGOS":     ("Lagos State",    "Centre of Excellence"),
    "ABUJA":     ("FCT Abuja",      "Centre of Unity"),
    "KANO":      ("Kano State",     "Centre of Commerce"),
    "KADUNA":    ("Kaduna State",   "State of Dialogue"),
    "RIVERS":    ("Rivers State",   "Treasure Base of the Nation"),
    "OGUN":      ("Ogun State",     "Gateway State"),
    "OYO":       ("Oyo State",      "Pace Setter State"),
    "ANAMBRA":   ("Anambra State",  "Light of the Nation"),
    "ENUGU":     ("Enugu State",    "Coal City State"),
    "DELTA":     ("Delta State",    "The Big Heart"),
    "ONDO":      ("Ondo State",     "Sunshine State"),
    "BENUE":     ("Benue State",    "Food Basket of the Nation"),
    "KOGI":      ("Kogi State",     "Confluence State"),
    "PLATEAU":   ("Plateau State",  "Home of Peace and Tourism"),
    "BAUCHI":    ("Bauchi State",   "Pearl of Tourism"),
    "GOMBE":     ("Gombe State",    "Jewel in the Savanna"),
    "YOBE":      ("Yobe State",     "Pride of the Sahara"),
    "BORNO":     ("Borno State",    "Home of Peace"),
    "ADAMAWA":   ("Adamawa State",  "Land of Beauty"),
    "TARABA":    ("Taraba State",   "Nature's Gift to the Nation"),
    "NASARAWA":  ("Nasarawa State", "Home of Solid Minerals"),
    "NIGER":     ("Niger State",    "Power State"),
    "KWARA":     ("Kwara State",    "State of Harmony"),
    "EKITI":     ("Ekiti State",    "Land of Honour and Integrity"),
    "OSUN":      ("Osun State",     "State of the Living Spring"),
    "EDO":       ("Edo State",      "Heartbeat of the Nation"),
    "IMO":       ("Imo State",      "Eastern Heartland"),
    "ABIA":      ("Abia State",     "God's Own State"),
    "EBONYI":    ("Ebonyi State",   "Salt of the Nation"),
    "BAYELSA":   ("Bayelsa State",  "Glory of All Lands"),
    "CROSS RIVER":("Cross River State", "The Peoples Paradise"),
    "AKWA IBOM": ("Akwa Ibom State","Land of Promise"),
    "KEBBI":     ("Kebbi State",    "Land of Equity"),
    "SOKOTO":    ("Sokoto State",   "Seat of the Caliphate"),
    "ZAMFARA":   ("Zamfara State",  "Farming is Our Pride"),
    "KATSINA":   ("Katsina State",  "Home of Hospitality"),
    "JIGAWA":    ("Jigawa State",   "Land of Opportunities"),
}


class ALPRService:
    """
    ALPR pipeline for Django.

    Flow:
      1. If YOLO is installed  → detect plate region → crop → OCR crop
      2. If no YOLO            → preprocess full image → OCR full image
      3. In both cases, extract plate text using Nigerian plate patterns
      4. Look up extracted plate in the database
      5. Return plate text + record (or "not found") regardless of DB result
    """

    MODEL_NAMES = ["YOLOv8", "YOLOv9", "YOLOv10", "Faster R-CNN", "SSD"]
    _detector   = None
    _ocr_reader = None

    # Nigerian plate patterns (covers most common formats):
    #   KJA-245-AA   ABC-123-XY   KTU-123-BC   ABUJA-ABC-123-DE
    # After stripping non-alphanumeric:
    #   letters(2-3) + digits(2-4) + letters(2-3)   e.g. KJA245AA
    _PLATE_PATTERN = re.compile(
        r'\b([A-Z]{2,3}[\s\-]?\d{2,4}[\s\-]?[A-Z]{2,3})\b'
    )

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def process_upload(cls, uploaded_file: UploadedFile, model_name: str) -> Dict[str, object]:
        if not uploaded_file:
            raise ValueError("No uploaded file provided")
        if model_name not in cls.MODEL_NAMES:
            raise ValueError(f"Unsupported model: {model_name}")

        uploaded_file.seek(0)
        image  = Image.open(uploaded_file).convert("RGB")
        width, height = image.size

        # Get all raw OCR text from the best preprocessing variant
        raw_text, plate_number, confidence, status = cls._run_pipeline_full(
            image, model_name, width, height
        )

        # If nothing was read at all, return a clear "no plate" result
        if status == "fallback" or not plate_number:
            return {
                "model_name":       model_name,
                "plate_number":     None,
                "confidence":       0.0,
                "status":           "no-plate-detected",
                "country":          None,
                "state":            None,
                "slogan":           None,
                "raw_text":         None,
                "record_found":     False,
                "vehicle_owner":    None,
                "vehicle_type":     None,
                "vehicle_model":    None,
                "vehicle_color":    None,
                "registration_number": None,
                "image_width":      width,
                "image_height":     height,
                "ocr_unavailable":  not cls._ocr_available(),
            }

        # Extract country, state, slogan from the raw OCR text
        plate_info = cls._extract_plate_info(raw_text, plate_number)

        # Look up the plate in the database
        record = cls._lookup_registered_vehicle(plate_number)

        result = {
            "model_name":       model_name,
            "plate_number":     plate_number,
            "confidence":       round(confidence, 3),
            "status":           status,
            "country":          plate_info.get("country"),
            "state":            plate_info.get("state"),
            "slogan":           plate_info.get("slogan"),
            "raw_text":         plate_info.get("raw_text"),
            "record_found":     False,
            "vehicle_owner":    None,
            "vehicle_type":     None,
            "vehicle_model":    None,
            "vehicle_color":    None,
            "registration_number": None,
            "image_width":      width,
            "image_height":     height,
            "ocr_unavailable":  False,
        }

        if record is not None:
            result.update({
                "record_found":        True,
                "status":              "registered",
                "vehicle_owner":       record["owner"],
                "vehicle_type":        record["vehicle_type"],
                "vehicle_model":       record["vehicle_model"],
                "vehicle_color":       record["vehicle_color"],
                "registration_number": record["registration_number"],
            })
        else:
            result["status"] = "not-registered"

        return result

    @classmethod
    def get_available_models(cls) -> List[str]:
        return list(cls.MODEL_NAMES)

    # ------------------------------------------------------------------ #
    #  Pipeline                                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def _run_pipeline_full(
        cls, image: Any, model_name: str, width: int, height: int
    ) -> Tuple[str, str, float, str]:
        """Returns (raw_text, plate_number, confidence, status)."""

        # Step 1 — YOLO detection + OCR on cropped plate region
        detection_result = cls._detect_plate_region(image, model_name)
        if detection_result:
            raw_text, plate_text, confidence = detection_result
            if plate_text:
                return raw_text, plate_text, confidence, "ocr-detected"

        # Step 2 — No YOLO; OCR on the full preprocessed image
        raw_text, plate_text, confidence = cls._ocr_full_image_with_raw(image)
        if plate_text:
            return raw_text, plate_text, confidence, "ocr-direct"

        # Step 3 — Nothing worked
        plate, conf, status = cls._fallback_plate_from_image(width, height)
        return "", plate, conf, status

    # Keep old _run_pipeline for backward compatibility
    @classmethod
    def _run_pipeline(cls, image: Any, model_name: str, width: int, height: int) -> Tuple[str, float, str]:
        _, plate, conf, status = cls._run_pipeline_full(image, model_name, width, height)
        return plate, conf, status

    # ------------------------------------------------------------------ #
    #  Full-image OCR — returns raw text + best plate                     #
    # ------------------------------------------------------------------ #

    @classmethod
    def _ocr_full_image_with_raw(cls, image: Any) -> Tuple[str, str, float]:
        """Returns (raw_text, plate_number, confidence)."""
        variants = cls._preprocess_variants(image)
        candidates = []  # (raw_text, plate, conf, score)

        # easyocr
        try:
            import easyocr
            import numpy as np
            if cls._ocr_reader is None:
                cls._ocr_reader = easyocr.Reader(["en"], gpu=False)
            for variant in variants:
                results = cls._ocr_reader.readtext(np.array(variant))
                raw = " ".join(t for _, t, _ in results)
                plate = cls._extract_plate_from_text(raw)
                if plate:
                    conf  = max((c for _, _, c in results), default=0.5)
                    score = cls._score_plate(plate)
                    candidates.append((raw, plate, float(conf), score))
                    if score >= 3:
                        break
        except Exception:
            pass

        # Tesseract
        try:
            import pytesseract
            configs = ['--psm 6 --oem 3', '--psm 11 --oem 3',
                       '--psm 3 --oem 3', '--psm 7 --oem 3']
            for variant in variants:
                for cfg in configs:
                    try:
                        raw   = pytesseract.image_to_string(variant, config=cfg)
                        plate = cls._extract_plate_from_text(raw)
                        if plate:
                            score = cls._score_plate(plate)
                            candidates.append((raw.strip(), plate, 0.70, score))
                            if score >= 3:
                                break
                    except Exception:
                        continue
                if any(c[3] >= 3 for c in candidates):
                    break
        except Exception:
            pass

        if not candidates:
            return "", "", 0.0

        best = max(candidates, key=lambda x: x[3])
        return best[0], best[1], best[2]

    # Wrapper keeping old signature
    @classmethod
    def _ocr_full_image(cls, image: Any) -> Tuple[str, float]:
        _, plate, conf = cls._ocr_full_image_with_raw(image)
        return plate, conf

    # ------------------------------------------------------------------ #
    #  Extract all plate fields from raw OCR text                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def _extract_plate_info(cls, raw_text: str, plate_number: str) -> Dict[str, str]:
        """
        Parse the raw OCR text of a Nigerian plate and extract:
          - country  (e.g. "Federal Republic of Nigeria")
          - state    (e.g. "Lagos State")
          - slogan   (e.g. "Centre of Excellence")
          - raw_text (cleaned version of what was read)
        """
        upper = raw_text.upper() if raw_text else ""

        country = None
        state   = None
        slogan  = None

        # ── Country ───────────────────────────────────────────────────────
        if "NIGERIA" in upper or "FEDERAL REPUBLIC" in upper:
            country = "Federal Republic of Nigeria"

        # ── State + slogan ─────────────────────────────────────────────────
        for keyword, (state_name, state_slogan) in NIGERIAN_STATES.items():
            if keyword in upper:
                state  = state_name
                slogan = state_slogan
                break

        # If state not found from OCR, try to infer from the plate prefix
        # Nigerian plates: first 2-3 letters are the state code
        if not state and plate_number:
            prefix = re.match(r'^([A-Z]{2,3})', plate_number.upper())
            if prefix:
                state, slogan = cls._state_from_prefix(prefix.group(1))

        # ── Clean raw text ─────────────────────────────────────────────────
        cleaned_lines = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line and len(line) > 1:
                cleaned_lines.append(line)
        clean = " | ".join(cleaned_lines) if cleaned_lines else raw_text

        return {
            "country":  country or "Nigeria",
            "state":    state,
            "slogan":   slogan,
            "raw_text": clean,
        }

    @staticmethod
    def _state_from_prefix(prefix: str) -> Tuple[Optional[str], Optional[str]]:
        """Infer state from Nigerian plate prefix letters."""
        PREFIX_MAP = {
            # Lagos
            "LA": ("Lagos State", "Centre of Excellence"),
            "LSD":("Lagos State", "Centre of Excellence"),
            "GGE":("Lagos State", "Centre of Excellence"),
            "KJA":("Lagos State", "Centre of Excellence"),
            "AAA":("Lagos State", "Centre of Excellence"),
            # FCT Abuja
            "AB": ("FCT Abuja",   "Centre of Unity"),
            "ABJ":("FCT Abuja",   "Centre of Unity"),
            # Kano
            "KN": ("Kano State",  "Centre of Commerce"),
            "KNA":("Kano State",  "Centre of Commerce"),
            # Kaduna
            "KD": ("Kaduna State","State of Dialogue"),
            "KDA":("Kaduna State","State of Dialogue"),
            # Rivers
            "RI": ("Rivers State","Treasure Base of the Nation"),
            "RSH":("Rivers State","Treasure Base of the Nation"),
            # Ogun
            "OG": ("Ogun State",  "Gateway State"),
            # Oyo
            "OY": ("Oyo State",   "Pace Setter State"),
            # Anambra
            "AN": ("Anambra State","Light of the Nation"),
            # Enugu
            "EN": ("Enugu State", "Coal City State"),
            # Delta
            "DL": ("Delta State", "The Big Heart"),
            # Ondo
            "ON": ("Ondo State",  "Sunshine State"),
            # Kogi
            "KG": ("Kogi State",  "Confluence State"),
            # Niger
            "MN": ("Niger State", "Power State"),
            # Kwara
            "KW": ("Kwara State", "State of Harmony"),
            # Edo
            "BE": ("Edo State",   "Heartbeat of the Nation"),
        }
        entry = PREFIX_MAP.get(prefix.upper())
        if entry:
            return entry
        return None, None

    @staticmethod
    def _score_plate(plate: str) -> int:
        """
        Score a candidate plate string. Higher = better match.
        Nigerian format: 2-3 letters + 2-4 digits + 2-3 letters = score 3
        Partial match (letters+digits but not full pattern) = score 1
        """
        if not plate:
            return 0
        # Full Nigerian pattern: GGE123ZY, KJA245AA, ABC123XY
        if re.match(r'^[A-Z]{2,3}[0-9]{2,4}[A-Z]{2,3}$', plate):
            return 3
        # Has both letters and digits
        has_alpha = bool(re.search(r'[A-Z]', plate))
        has_digit = bool(re.search(r'[0-9]', plate))
        if has_alpha and has_digit:
            return 1
        return 0

    @staticmethod
    def _preprocess_variants(image: Any) -> List[Any]:
        """
        Return preprocessed versions of the image, best variants first.
        gray_2x (2× upscaled grayscale) is the most reliable for Nigerian
        plates — it handles both blue and black text well.
        """
        from PIL import ImageOps, ImageFilter, ImageEnhance

        gray = image.convert("L")
        w, h  = image.size
        r, g, b = image.convert("RGB").split()

        variants = []

        # ── Best performers first ────────────────────────────────────────

        # #1 — 2× upscaled grayscale (best all-round for Nigerian plates)
        gray_2x = gray.resize((w * 2, h * 2), Image.LANCZOS)
        variants.append(gray_2x)

        # #2 — 3× upscale (for small / low-res images)
        variants.append(gray.resize((w * 3, h * 3), Image.LANCZOS))

        # #3 — 2× upscale + auto-contrast
        variants.append(ImageOps.autocontrast(gray_2x, cutoff=2))

        # #4 — Red channel 2× (good contrast for any dark text colour)
        variants.append(r.resize((w * 2, h * 2), Image.LANCZOS))

        # #5 — Plain grayscale
        variants.append(gray)

        # #6 — Auto-contrast + sharpen
        contrast = ImageOps.autocontrast(gray, cutoff=2)
        variants.append(contrast.filter(ImageFilter.SHARPEN))

        # #7 — High contrast (2.5×) + sharpen
        enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
        variants.append(enhanced.filter(ImageFilter.SHARPEN))

        # #8 — Inverted blue channel 2× (helps when plate text is pure blue)
        inv_blue_2x = ImageOps.invert(b).resize((w * 2, h * 2), Image.LANCZOS)
        variants.append(inv_blue_2x)

        return variants

    # ------------------------------------------------------------------ #
    #  YOLO detection                                                      #
    # ------------------------------------------------------------------ #

    @classmethod
    def _detect_plate_region(cls, image: Any, model_name: str) -> Optional[Tuple[str, float]]:
        try:
            import numpy as np
        except ImportError:
            return None
        try:
            from ultralytics import YOLO
        except ImportError:
            return None

        detector = cls._load_detector(model_name)
        if detector is None:
            return None

        try:
            results = detector(np.array(image), imgsz=640, conf=0.25, stream=False)[0]
        except Exception:
            return None

        detected_boxes = []
        for box in getattr(results, "boxes", []):
            conf = float(box.conf[0]) if getattr(box, "conf", None) is not None else 0.0
            if conf < 0.2:
                continue
            names      = getattr(results, "names", {})
            label_name = names.get(int(box.cls[0]), "") if isinstance(names, dict) else names[int(box.cls[0])]
            label_text = (label_name or "").lower()
            if "plate" in label_text or "license" in label_text or "car" in label_text:
                detected_boxes.append((box, conf))

        if not detected_boxes:
            return None

        top_box, top_conf = detected_boxes[0]
        x1, y1, x2, y2   = map(int, top_box.xyxy[0].tolist())
        cropped = image.crop((x1, y1, x2, y2))
        if cropped.size[0] == 0 or cropped.size[1] == 0:
            return None

        plate_text, ocr_conf = cls._ocr_full_image(cropped)
        if plate_text:
            return plate_text, round(max(top_conf, ocr_conf), 3)
        return None

    @classmethod
    def _load_detector(cls, model_name: str):
        if cls._detector is not None:
            return cls._detector
        model_file = "yolov8n.pt"
        if "YOLOv9"      in model_name: model_file = "yolov9c.pt"
        elif "YOLOv10"   in model_name: model_file = "yolov10n.pt"
        elif "Faster R-CNN" in model_name: model_file = "fasterrcnn_resnet50_fpn_v2.pt"
        elif "SSD"       in model_name: model_file = "ssd300_vgg16.pt"
        try:
            from ultralytics import YOLO
            cls._detector = YOLO(model_file)
            return cls._detector
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #  Text extraction helpers                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def _extract_plate_from_text(cls, text: str) -> str:
        """
        Given raw OCR text (may be multi-line, may contain state/country names),
        extract the most likely plate number.

        Nigerian plate format: 3-letters  3-digits  2-letters
          e.g.  GGE-123ZY   KJA 245 AA   ABC-123-XY
        """
        if not text:
            return ""

        upper = text.upper()

        # ── Strategy 1: direct Nigerian plate regex ─────────────────────
        # Full plate in one token e.g. "GGE123ZY" or "GGE-123-ZY"
        match = cls._PLATE_PATTERN.search(upper)
        if match:
            candidate = re.sub(r"[^A-Z0-9]", "", match.group(1))
            if 5 <= len(candidate) <= 10:
                return candidate

        # ── Strategy 2: sliding window over cleaned tokens ───────────────
        # Remove noise words and split into tokens
        cleaned_text = upper
        for noise in ("FEDERAL REPUBLIC OF NIGERIA", "CENTRE OF EXCELLENCE",
                      "REPUBLIC OF NIGERIA", "NIGERIA", "FEDERAL",
                      "LAGOS", "ABUJA", "KADUNA", "KANO", "RIVERS", "OGUN",
                      "OYO", "ANAMBRA", "ENUGU", "DELTA", "ONDO", "BENUE",
                      "KOGI", "PLATEAU", "BAUCHI", "GOMBE", "YOBE", "BORNO",
                      "ADAMAWA", "TARABA", "NASARAWA", "NIGER", "KWARA",
                      "EKITI", "OSUN", "EDO", "IMO", "ABIA", "EBONYI",
                      "BAYELSA", "FRSC", "VIO", "GOVERNMENT",
                      "CENTRE", "EXCELLENCE", "UNITY"):
            cleaned_text = cleaned_text.replace(noise, " ")

        # Collect all alphanumeric tokens
        tokens = [re.sub(r"[^A-Z0-9]", "", t)
                  for t in re.split(r"[\s\-_/\\|,.]+", cleaned_text)]
        tokens = [t for t in tokens if t]  # drop empty

        # Try single tokens first
        for token in tokens:
            if 5 <= len(token) <= 10:
                has_alpha = bool(re.search(r"[A-Z]", token))
                has_digit = bool(re.search(r"[0-9]", token))
                if has_alpha and has_digit:
                    return token

        # Try joining adjacent token pairs (handles "GGE" + "123ZY")
        for i in range(len(tokens) - 1):
            joined = tokens[i] + tokens[i + 1]
            if 5 <= len(joined) <= 10:
                has_alpha = bool(re.search(r"[A-Z]", joined))
                has_digit = bool(re.search(r"[0-9]", joined))
                if has_alpha and has_digit:
                    return joined

        # Try joining three adjacent tokens (handles "GGE" + "123" + "ZY")
        for i in range(len(tokens) - 2):
            joined = tokens[i] + tokens[i + 1] + tokens[i + 2]
            if 5 <= len(joined) <= 10:
                has_alpha = bool(re.search(r"[A-Z]", joined))
                has_digit = bool(re.search(r"[0-9]", joined))
                if has_alpha and has_digit:
                    return joined

        return ""

    @staticmethod
    def _normalize_plate_text(text: str) -> str:
        """Simple normaliser used by the easyocr path for individual text boxes."""
        cleaned = re.sub(r"[^A-Za-z0-9]", "", text.upper())
        # Accept 4-10 chars that contain both letters and digits
        if 4 <= len(cleaned) <= 10:
            has_letters = bool(re.search(r"[A-Z]", cleaned))
            has_digits  = bool(re.search(r"[0-9]", cleaned))
            if has_letters and has_digits:
                return cleaned
        return ""

    @staticmethod
    def _extract_plate_from_filename(file_name: Optional[str]) -> Optional[str]:
        if not file_name:
            return None
        match = re.search(r"([A-Za-z]{2,3}[\-\s]?\d{2,4}[\-\s]?[A-Za-z]{2,3})", file_name.upper())
        if not match:
            return None
        plate = re.sub(r"[^A-Za-z0-9]", "", match.group(1))
        return plate if 5 <= len(plate) <= 10 else None

    # ------------------------------------------------------------------ #
    #  Database lookup                                                     #
    # ------------------------------------------------------------------ #

    @classmethod
    def _lookup_registered_vehicle(cls, plate_number: str) -> Optional[Dict[str, Any]]:
        if not plate_number:
            return None
        normalized = plate_number.strip().upper()
        record = CarRegisteration.objects.filter(plate_number__icontains=normalized).first()
        if record is None:
            return None
        return {
            "owner":               str(record.owner.full_name),
            "vehicle_type":        record.vehicle_type,
            "vehicle_model":       record.model,
            "vehicle_color":       record.color,
            "registration_number": record.plate_number,
        }

    # ------------------------------------------------------------------ #
    #  OCR availability check                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ocr_available() -> bool:
        try:
            import pytesseract
            from PIL import Image as PILImage
            tiny = PILImage.new("RGB", (10, 10), color=(255, 255, 255))
            pytesseract.image_to_string(tiny)
            return True
        except Exception:
            pass
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            pass
        try:
            from ultralytics import YOLO  # noqa: F401
            return True
        except ImportError:
            pass
        return False

    # ------------------------------------------------------------------ #
    #  Fallback (dimension-based — only used when OCR completely fails)   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fallback_plate_from_image(width: int, height: int) -> Tuple[str, float, str]:
        prefix = "AB"
        middle = (width * 3 + height) % 900 + 100
        suffix = chr(65 + ((width + height) % 8))
        return f"{prefix}{middle}{suffix}", 0.35, "fallback"
