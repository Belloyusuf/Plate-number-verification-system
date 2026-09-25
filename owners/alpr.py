import re
import os
import sys

from typing import Any, Dict, List, Optional, Tuple

from django.core.files.uploadedfile import UploadedFile
from PIL import Image

from .models import CarRegisteration

# ── Windows Tesseract path ─────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except ImportError:
        pass


# ── Nigerian state registry ────────────────────────────────────────────────────
NIGERIAN_STATES = {
    "LAGOS":      ("Lagos State",       "Centre of Excellence"),
    "ABUJA":      ("FCT Abuja",         "Centre of Unity"),
    "FCT":        ("FCT Abuja",         "Centre of Unity"),
    "KANO":       ("Kano State",        "Centre of Commerce"),
    "KADUNA":     ("Kaduna State",      "State of Dialogue"),
    "RIVERS":     ("Rivers State",      "Treasure Base of the Nation"),
    "OGUN":       ("Ogun State",        "Gateway State"),
    "OYO":        ("Oyo State",         "Pace Setter State"),
    "ANAMBRA":    ("Anambra State",     "Light of the Nation"),
    "ENUGU":      ("Enugu State",       "Coal City State"),
    "DELTA":      ("Delta State",       "The Big Heart"),
    "ONDO":       ("Ondo State",        "Sunshine State"),
    "BENUE":      ("Benue State",       "Food Basket of the Nation"),
    "KOGI":       ("Kogi State",        "Confluence State"),
    "PLATEAU":    ("Plateau State",     "Home of Peace and Tourism"),
    "BAUCHI":     ("Bauchi State",      "Pearl of Tourism"),
    "GOMBE":      ("Gombe State",       "Jewel in the Savanna"),
    "YOBE":       ("Yobe State",        "Pride of the Sahara"),
    "BORNO":      ("Borno State",       "Home of Peace"),
    "ADAMAWA":    ("Adamawa State",     "Land of Beauty"),
    "TARABA":     ("Taraba State",      "Nature's Gift to the Nation"),
    "NASARAWA":   ("Nasarawa State",    "Home of Solid Minerals"),
    "NIGER":      ("Niger State",       "Power State"),
    "KWARA":      ("Kwara State",       "State of Harmony"),
    "EKITI":      ("Ekiti State",       "Land of Honour and Integrity"),
    "OSUN":       ("Osun State",        "State of the Living Spring"),
    "EDO":        ("Edo State",         "Heartbeat of the Nation"),
    "IMO":        ("Imo State",         "Eastern Heartland"),
    "ABIA":       ("Abia State",        "God's Own State"),
    "EBONYI":     ("Ebonyi State",      "Salt of the Nation"),
    "BAYELSA":    ("Bayelsa State",     "Glory of All Lands"),
    "CROSS RIVER":("Cross River State", "The Peoples Paradise"),
    "AKWA IBOM":  ("Akwa Ibom State",   "Land of Promise"),
    "KEBBI":      ("Kebbi State",       "Land of Equity"),
    "SOKOTO":     ("Sokoto State",      "Seat of the Caliphate"),
    "ZAMFARA":    ("Zamfara State",     "Farming is Our Pride"),
    "KATSINA":    ("Katsina State",     "Home of Hospitality"),
    "JIGAWA":     ("Jigawa State",      "Land of Opportunities"),
}

# Plate-prefix → state (for when OCR misses the state name)
PREFIX_TO_STATE = {
    # Lagos
    "AA": "LAGOS", "AB": "LAGOS", "AC": "LAGOS", "AD": "LAGOS",
    "AE": "LAGOS", "AF": "LAGOS", "AG": "LAGOS", "AH": "LAGOS",
    "GGE": "LAGOS", "KJA": "LAGOS", "LND": "LAGOS", "LSD": "LAGOS",
    "APP": "LAGOS", "EPE": "LAGOS",
    # FCT Abuja
    "ABJ": "ABUJA", "FCT": "ABUJA",
    # Kano
    "KN": "KANO", "KNA": "KANO",
    # Kaduna
    "KD": "KADUNA", "KDA": "KADUNA",
    # Rivers
    "RI": "RIVERS", "RSH": "RIVERS",
    # Ogun
    "OG": "OGUN", "OGD": "OGUN",
    # Oyo
    "OY": "OYO",
    # Anambra
    "AN": "ANAMBRA",
    # Enugu
    "EN": "ENUGU",
    # Delta
    "DL": "DELTA",
    # Ondo
    "ON": "ONDO",
    # Kogi
    "KG": "KOGI",
    # Niger
    "MN": "NIGER",
    # Kwara
    "KW": "KWARA",
    # Edo
    "BE": "EDO",
    # Imo
    "IM": "IMO",
    # Abia
    "AA": "ABIA",
    # Plateau
    "PL": "PLATEAU",
}

# ── Common OCR character confusion corrections ─────────────────────────────────
# In the LETTER positions of a plate:  digits are misread as letters
# In the DIGIT positions:              letters are misread as digits
# Pattern for Nigerian plate: LLL DDD LL  (L=letter, D=digit)
# We correct based on position within the extracted token.
LETTER_FIXES = {"0": "O", "1": "I", "5": "S", "6": "G", "8": "B"}
DIGIT_FIXES  = {"O": "0", "I": "1", "S": "5", "G": "6", "B": "8", "Z": "2", "A": "4", "D": "0", "Q": "0"}


class ALPRService:
    """
    ALPR pipeline for Django.
    Reads a plate image, extracts the plate number + all plate metadata
    (country, state, slogan), then checks the vehicle database.
    """

    MODEL_NAMES = ["YOLOv8", "YOLOv9", "YOLOv10", "Faster R-CNN", "SSD"]
    _detector   = None
    _ocr_reader = None

    _PLATE_RE = re.compile(r'\b([A-Z]{2,3}[\s\-]?\d{2,4}[\s\-]?[A-Z]{2,3})\b')

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
        image         = Image.open(uploaded_file).convert("RGB")
        width, height = image.size

        raw_text, plate_number, confidence, status = cls._run_pipeline_full(
            image, model_name, width, height
        )

        if status == "fallback" or not plate_number:
            return {
                "model_name":          model_name,
                "plate_number":        None,
                "confidence":          0.0,
                "status":              "no-plate-detected",
                "country":             None,
                "state":               None,
                "slogan":              None,
                "raw_text":            None,
                "record_found":        False,
                "vehicle_owner":       None,
                "vehicle_type":        None,
                "vehicle_model":       None,
                "vehicle_color":       None,
                "registration_number": None,
                "image_width":         width,
                "image_height":        height,
                "ocr_unavailable":     not cls._ocr_available(),
            }

        plate_info = cls._extract_plate_info(raw_text, plate_number)
        record     = cls._lookup_registered_vehicle(plate_number)

        result = {
            "model_name":          model_name,
            "plate_number":        plate_number,
            "confidence":          round(confidence, 3),
            "status":              status,
            "country":             plate_info.get("country"),
            "state":               plate_info.get("state"),
            "slogan":              plate_info.get("slogan"),
            "raw_text":            plate_info.get("raw_text"),
            "record_found":        False,
            "vehicle_owner":       None,
            "vehicle_type":        None,
            "vehicle_model":       None,
            "vehicle_color":       None,
            "registration_number": None,
            "image_width":         width,
            "image_height":        height,
            "ocr_unavailable":     False,
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

        detection_result = cls._detect_plate_region(image, model_name)
        if detection_result:
            raw_text, plate_text, confidence = detection_result
            if plate_text:
                return raw_text, plate_text, confidence, "ocr-detected"

        raw_text, plate_text, confidence = cls._ocr_full_image_with_raw(image)
        if plate_text:
            return raw_text, plate_text, confidence, "ocr-direct"

        plate, conf, status = cls._fallback_plate_from_image(width, height)
        return "", plate, conf, status

    @classmethod
    def _run_pipeline(cls, image: Any, model_name: str, width: int, height: int) -> Tuple[str, float, str]:
        _, plate, conf, status = cls._run_pipeline_full(image, model_name, width, height)
        return plate, conf, status

    # ------------------------------------------------------------------ #
    #  OCR                                                                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def _ocr_full_image_with_raw(cls, image: Any) -> Tuple[str, str, float]:
        """Returns (raw_text, plate_number, confidence)."""
        variants   = cls._preprocess_variants(image)
        candidates = []  # (raw_text, plate, conf, score)

        # easyocr
        try:
            import easyocr
            import numpy as np
            if cls._ocr_reader is None:
                cls._ocr_reader = easyocr.Reader(["en"], gpu=False)
            for variant in variants:
                results = cls._ocr_reader.readtext(np.array(variant))
                raw     = " ".join(t for _, t, _ in results)
                plate   = cls._extract_plate_from_text(raw)
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
            configs = [
                '--psm 6 --oem 3',
                '--psm 11 --oem 3',
                '--psm 3 --oem 3',
                '--psm 7 --oem 3',
            ]
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

    @classmethod
    def _ocr_full_image(cls, image: Any) -> Tuple[str, float]:
        _, plate, conf = cls._ocr_full_image_with_raw(image)
        return plate, conf

    # ------------------------------------------------------------------ #
    #  Preprocessing                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _preprocess_variants(image: Any) -> List[Any]:
        from PIL import ImageOps, ImageFilter, ImageEnhance
        gray        = image.convert("L")
        w, h        = image.size
        r, g, b     = image.convert("RGB").split()

        gray_2x     = gray.resize((w * 2, h * 2), Image.LANCZOS)
        gray_3x     = gray.resize((w * 3, h * 3), Image.LANCZOS)
        inv_blue_2x = ImageOps.invert(b).resize((w * 2, h * 2), Image.LANCZOS)

        return [
            gray_2x,                                                           # #1 best all-round
            gray_3x,                                                           # #2 high-res
            ImageOps.autocontrast(gray_2x, cutoff=2),                         # #3 contrast boost
            r.resize((w * 2, h * 2), Image.LANCZOS),                          # #4 red channel
            gray,                                                              # #5 plain gray
            ImageOps.autocontrast(gray, cutoff=2).filter(ImageFilter.SHARPEN),# #6 contrast+sharp
            ImageEnhance.Contrast(gray).enhance(2.5).filter(ImageFilter.SHARPEN), # #7 high contrast
            inv_blue_2x,                                                       # #8 inverted blue
        ]

    # ------------------------------------------------------------------ #
    #  Plate text extraction + correction                                  #
    # ------------------------------------------------------------------ #

    @classmethod
    def _extract_plate_from_text(cls, text: str) -> str:
        if not text:
            return ""
        upper = text.upper()

        # Strategy 1 — direct regex match
        match = cls._PLATE_RE.search(upper)
        if match:
            candidate = re.sub(r"[^A-Z0-9]", "", match.group(1))
            if 5 <= len(candidate) <= 10:
                return cls._correct_plate(candidate)

        # Strategy 2 — remove noise words then try tokens + token joins
        cleaned = upper
        for noise in (
            "FEDERAL REPUBLIC OF NIGERIA", "CENTRE OF EXCELLENCE",
            "REPUBLIC OF NIGERIA", "NIGERIA", "FEDERAL",
            "LAGOS", "ABUJA", "KADUNA", "KANO", "RIVERS", "OGUN",
            "OYO", "ANAMBRA", "ENUGU", "DELTA", "ONDO", "BENUE",
            "KOGI", "PLATEAU", "BAUCHI", "GOMBE", "YOBE", "BORNO",
            "ADAMAWA", "TARABA", "NASARAWA", "NIGER", "KWARA",
            "EKITI", "OSUN", "EDO", "IMO", "ABIA", "EBONYI",
            "BAYELSA", "FRSC", "VIO", "GOVERNMENT",
            "CENTRE", "EXCELLENCE", "UNITY",
        ):
            cleaned = cleaned.replace(noise, " ")

        tokens = [re.sub(r"[^A-Z0-9]", "", t)
                  for t in re.split(r"[\s\-_/\\|,.]+", cleaned)]
        tokens = [t for t in tokens if t]

        def is_plate_like(s):
            return (5 <= len(s) <= 10
                    and bool(re.search(r"[A-Z]", s))
                    and bool(re.search(r"[0-9]", s)))

        # Single token
        for tok in tokens:
            if is_plate_like(tok):
                return cls._correct_plate(tok)

        # Two adjacent tokens
        for i in range(len(tokens) - 1):
            joined = tokens[i] + tokens[i + 1]
            if is_plate_like(joined):
                return cls._correct_plate(joined)

        # Three adjacent tokens
        for i in range(len(tokens) - 2):
            joined = tokens[i] + tokens[i + 1] + tokens[i + 2]
            if is_plate_like(joined):
                return cls._correct_plate(joined)

        return ""

    @staticmethod
    def _correct_plate(plate: str) -> str:
        """
        Apply position-aware OCR correction to a Nigerian plate candidate.

        Nigerian format:  L L L  D D D  L L
                          0 1 2  3 4 5  6 7  (indices, 0-based)

        - Positions 0-2 (prefix letters): digits misread as letters → fix
        - Positions 3-5 (digits):         letters misread as digits → fix
        - Positions 6-7 (suffix letters): digits misread as letters → fix
        """
        p = plate.upper()

        # Only apply position-aware correction if the plate is exactly 8 chars
        # (most common Nigerian format: 3 letters + 3 digits + 2 letters)
        if len(p) == 8:
            corrected = list(p)
            # Prefix (0-2): should be letters
            for i in range(3):
                corrected[i] = LETTER_FIXES.get(corrected[i], corrected[i])
            # Middle (3-5): should be digits
            for i in range(3, 6):
                corrected[i] = DIGIT_FIXES.get(corrected[i], corrected[i])
            # Suffix (6-7): should be letters
            for i in range(6, 8):
                corrected[i] = LETTER_FIXES.get(corrected[i], corrected[i])
            return "".join(corrected)

        # For other lengths (7, 9, 10) just apply broad corrections
        # based on whether each character looks like it's in a letter or digit run
        segments = re.split(r'(\d+)', p)  # split into letter/digit runs
        out = []
        for seg in segments:
            if not seg:
                continue
            if seg[0].isdigit():
                # digit run — fix letters that look like digits
                out.append("".join(DIGIT_FIXES.get(c, c) for c in seg))
            else:
                # letter run — fix digits that look like letters
                out.append("".join(LETTER_FIXES.get(c, c) for c in seg))
        return "".join(out)

    @staticmethod
    def _score_plate(plate: str) -> int:
        """Score a candidate plate. Nigerian full pattern = 3, partial = 1."""
        if not plate:
            return 0
        if re.match(r'^[A-Z]{2,3}[0-9]{2,4}[A-Z]{2,3}$', plate):
            return 3
        if bool(re.search(r'[A-Z]', plate)) and bool(re.search(r'[0-9]', plate)):
            return 1
        return 0

    # ------------------------------------------------------------------ #
    #  Plate metadata extraction (country, state, slogan)                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def _extract_plate_info(cls, raw_text: str, plate_number: str) -> Dict[str, str]:
        upper   = raw_text.upper() if raw_text else ""
        country = None
        state   = None
        slogan  = None

        # Country
        if "NIGERIA" in upper or "FEDERAL REPUBLIC" in upper:
            country = "Federal Republic of Nigeria"

        # State from OCR text
        for keyword, (state_name, state_slogan) in NIGERIAN_STATES.items():
            if keyword in upper:
                state  = state_name
                slogan = state_slogan
                break

        # State from plate prefix (only when OCR text didn't find the state name)
        if not state and plate_number:
            for plen in (3, 2):
                raw_prefix   = plate_number[:plen].upper()
                fixed_prefix = "".join(LETTER_FIXES.get(c, c) for c in raw_prefix)
                for pfx in (raw_prefix, fixed_prefix):
                    state_key = PREFIX_TO_STATE.get(pfx)
                    if state_key and state_key in NIGERIAN_STATES:
                        state, slogan = NIGERIAN_STATES[state_key]
                        break
                if state:
                    break

        # Always set country for Nigerian plates
        if not country:
            country = "Federal Republic of Nigeria"

        # Clean raw text for display
        cleaned_lines = []
        if raw_text:
            cleaned_lines = [l.strip() for l in raw_text.splitlines() if l.strip() and len(l.strip()) > 1]
        clean = " | ".join(cleaned_lines) if cleaned_lines else ""

        return {
            "country":  country,
            "state":    state,
            "slogan":   slogan,
            "raw_text": clean,
        }

    # ------------------------------------------------------------------ #
    #  YOLO detection                                                      #
    # ------------------------------------------------------------------ #

    @classmethod
    def _detect_plate_region(cls, image: Any, model_name: str) -> Optional[Tuple[str, str, float]]:
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
            if any(kw in (label_name or "").lower() for kw in ("plate", "license", "car")):
                detected_boxes.append((box, conf))

        if not detected_boxes:
            return None

        top_box, top_conf = detected_boxes[0]
        x1, y1, x2, y2   = map(int, top_box.xyxy[0].tolist())
        cropped = image.crop((x1, y1, x2, y2))
        if cropped.size[0] == 0 or cropped.size[1] == 0:
            return None

        raw_text, plate_text, ocr_conf = cls._ocr_full_image_with_raw(cropped)
        if plate_text:
            return raw_text, plate_text, round(max(top_conf, ocr_conf), 3)
        return None

    @classmethod
    def _load_detector(cls, model_name: str):
        if cls._detector is not None:
            return cls._detector
        file_map = {
            "YOLOv9": "yolov9c.pt", "YOLOv10": "yolov10n.pt",
            "Faster R-CNN": "fasterrcnn_resnet50_fpn_v2.pt", "SSD": "ssd300_vgg16.pt",
        }
        model_file = next((v for k, v in file_map.items() if k in model_name), "yolov8n.pt")
        try:
            from ultralytics import YOLO
            cls._detector = YOLO(model_file)
            return cls._detector
        except Exception:
            return None

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
    #  OCR availability                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ocr_available() -> bool:
        try:
            import pytesseract
            from PIL import Image as PILImage
            pytesseract.image_to_string(PILImage.new("RGB", (10, 10), color=255))
            return True
        except Exception:
            pass
        for lib in ("easyocr", "ultralytics"):
            try:
                __import__(lib)
                return True
            except ImportError:
                pass
        return False

    # ------------------------------------------------------------------ #
    #  Fallback                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fallback_plate_from_image(width: int, height: int) -> Tuple[str, float, str]:
        prefix = "AB"
        middle = (width * 3 + height) % 900 + 100
        suffix = chr(65 + ((width + height) % 8))
        return f"{prefix}{middle}{suffix}", 0.35, "fallback"
