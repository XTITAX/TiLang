import re

def tokenize_line(line):
    line = line.strip()

    if not line or line.startswith("#"):
        return None, None

    if line.startswith("print("):
        return "print", line[6:-1]
    elif line == "que()":
        return "que", None
    elif line.startswith("delay("):
        return "delay", int(line[6:-1])
    elif line == "bye()":
        return "bye", None
    elif "=" in line and not line.startswith("if "):  # не путаем с if
        var, value = line.split("=", 1)
        return "assign", (var.strip(), value.strip())
    elif line.startswith("input("):
        return "input", line
    elif line.startswith("import "):
        return "import", line.split(" ", 1)[1].strip()
    if line.strip().startswith("//"):
        return ("comment", "")
    elif re.match(r"class\s*\(", line):  # class (hello, med) {
        return "class_start", line
    elif line == "}":
        return "class_end", None
    elif line.startswith("if ") and line.endswith("{"):
        condition = line[3:-1].strip()  # вырезаем if и {
        return "if_start", condition
    elif line == "}":
        return "block_end", None
    else:
        return "unknown", line
