# --- 1. รายการของเสีย (Defects) ---
DEFECT_LIST = [
    "Bubble", "Mashed", "Dent cap", "Dent body", "Loose",
    "Rough edge", "Ink speck", "Soiled", "Dirty",
    "Skewing", "Machine breakdown"
]

# --- 2. การกำหนดสีตามสถานะ (Status Colors) ---
# แก้ไขสีตามที่คุณนูระบุไว้
STATUS_COLORS = {
    "AF": "#2ecc71",  # สีเขียว
    "Sort": "#f1c40f",  # สีเหลือง
    "PS": "#e67e22",  # สีส้ม
    "HP": "#3498db",  # สีฟ้า
    "HUP": "#2980b9",  # สีน้ำเงิน
    "HFX": "#9b59b6",  # สีม่วง
    "Scrap": "#e74c3c"  # สีแดง
}

# --- 3. ข้อมูลสายการผลิต (Production Lines) ---
LINES = [f"H5{i:02d}" for i in range(1, 14)]

CUSTOMER_NAMES = [
    "ACG NORTH AMERCA LLC",
    "FAME Pharma Pte ltd",
    "PT.ACG Indonesia",
    "COMMUNITY PHARMACY PUBLIC",
    "ERNEST CHEMIST LTD",
    "Gel strength Co Ltd (Head office)"
]

METAL_DETECTOR_OPTIONS = ["Normal", "Iron Oxide"]

COUNTRIES = [
    "Thailand", "Indonesia", "USA", "Ghana",
    "Myanmar", "Singapore", "Vietnam"
]

BOX_PACKING_OPTIONS = [
    "Box 660", "Box 675", "Box 705", "Box 705+Liner",
    "Box 760+EPS Sheet", "Box Tabsule", "Box Fsample"
]

# COLUMNS สำหรับจัดแผน
PLAN_COLUMNS = [
    "line", "batch number", "sap batch", "production order",
    "inspection lot", "sales order", "sales order item", "fert code",
    "semifinish code", "item qty", "need af box", "customer name",
    "planned finish_date", "to be desp on", "metal detector", "print type",
    "country", "box packing", "ink cap", "roller des cap", "ink body",
    "roller des body", "batch status"
]

# รายชื่อหมึก (Ink Options)
INK_OPTIONS = [
    "-", "RMI010004 Black ACG", "RMI010021 White ACG", "RMI010182 Black ACG/TEK",
    "RMI010017 Red ACG", "RMI010002 Black TEK", "RMI010057 Green TEK", "RMI010033 Yellow/Gold TEK"
]

BATCH_STATUS = ["Running", "Finish"]

BOX_STATUS = ["AF", "HP", "HUP", "Sort", "PS", "Scrap", "HFX"]
