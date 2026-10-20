"""Read cell values from public XLSX tables without third-party dependencies."""
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

def read_xlsx(path):
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.itertext()) for t in root.findall("s:si", NS)]
        sheets = sorted(n for n in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+.xml", n))
        return [_read_sheet(archive.read(sheet), strings) for sheet in sheets]

def _read_sheet(xml, strings):
    rows = []
    for row in ET.fromstring(xml).findall(".//s:sheetData/s:row", NS):
        values = {}
        for cell in row.findall("s:c", NS):
            column = re.sub(r"\d", "", cell.attrib["r"])
            value = cell.find("s:v", NS)
            text = value.text if value is not None else ""
            if cell.attrib.get("t") == "s":
                text = strings[int(text)]
            if cell.attrib.get("t") == "inlineStr":
                text = "".join(cell.find("s:is", NS).itertext())
            values[column] = text
        rows.append(values)
    return rows

if __name__ == "__main__":
    import json, sys
    for name in sys.argv[1:]:
        sheets = read_xlsx(Path(name))
        print(name, [len(s) for s in sheets])
        print(json.dumps(sheets[0][:8], ensure_ascii=False, indent=2))
