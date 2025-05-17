import os
import re
from lexer import tokenize_line

def safe_c_expr(expr):
    if '+' in expr and '"' in expr:
        parts = [p.strip() for p in expr.split('+')]
        fmt = ""
        args = []
        for part in parts:
            if part.startswith('"') and part.endswith('"'):
                fmt += part.strip('"')
            else:
                fmt += "%s"
                args.append(part)
        return f'"{fmt}\\n"{", " + ", ".join(args) if args else ""}'
    elif expr.startswith('"') and expr.endswith('"'):
        return expr[:-1] + '\\n"'
    return expr.replace("**", "^")

class CCompiler:
    def __init__(self):
        self.classes = {}
        self.output = []
        self.includes = set(["#include <stdio.h>", "#include <stdlib.h>"])
        self.indent = "    "
        self.imported_files = set()
        self.lines = []
        self.funcs = []
        self.main_body = []

    def compile_script(self, path):
        self.includes.add("#include <windows.h>")
        self.imported_files = set()
        self.lines = []
        self.funcs = []
        self.main_body = []

        self.process_file(path)

        self.main_body.append(f'{self.indent}SetConsoleOutputCP(CP_UTF8);')

        self.i = 0
        while self.i < len(self.lines):
            token, value = tokenize_line(self.lines[self.i])
            if token == "print":
                self.main_body.append(f'{self.indent}printf({safe_c_expr(value)});')
            elif token == "que":
                self.main_body.append(f'{self.indent}printf("Нажмите Enter для продолжения...");')
                self.main_body.append(f'{self.indent}getchar();')
            elif token == "delay":
                self.main_body.append(f'{self.indent}Sleep({value});')
            elif token == "bye":
                self.main_body.append(f'{self.indent}return 0;')
            elif token == "assign":
                var, val = value
                self.main_body.append(f'{self.indent}int {var} = {safe_c_expr(val)};')
            elif token == "input":
                self.main_body.append(f'{self.indent}// input: {value}')
            elif token == "if_start":
                self.i = self.handle_if(self.lines, self.i, scope="main")
                continue
            elif token == "class_start":
                self.i = self.handle_class(self.lines, self.i)
                continue
            elif token == "unknown":
                if "(" in value and value.endswith(")"):
                    self.handle_class_call(value, scope="main")
                else:
                    print(f"[?] Неизвестная строка: {value}")
            self.i += 1

        self.output = []
        self.output.append("\n".join(sorted(self.includes)))
        self.output.append("")
        self.output.extend(self.funcs)
        self.output.append("int main() {")
        self.output.extend(self.main_body)
        self.output.append(f'{self.indent}return 0;')
        self.output.append("}")

    def process_file(self, path):
        abs_path = os.path.abspath(path)
        if abs_path in self.imported_files:
            return
        self.imported_files.add(abs_path)

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                import_path = stripped.split("import ", 1)[1].strip()
                if not import_path.endswith(".tl"):
                    import_path = os.path.join(import_path, "__init__.tl")
                self.process_file(import_path)
            else:
                self.lines.append(line)

    def handle_if(self, lines, i, scope="main"):
        token, condition = tokenize_line(lines[i])
        i += 1
        body = []
        depth = 1
        while i < len(lines) and depth > 0:
            t, v = tokenize_line(lines[i])
            if t == "if_start":
                depth += 1
            elif t == "block_end":
                depth -= 1
                if depth == 0:
                    break
            body.append(lines[i])
            i += 1
        block = []
        block.append(f'{self.indent}if ({safe_c_expr(condition)}) {{')
        for line in body:
            token, value = tokenize_line(line)
            stmt = self.get_line_from_token(token, value, scope)
            block.append(stmt)
        block.append(f'{self.indent}}}')
        if scope == "main":
            self.main_body.extend(block)
        else:
            self.funcs.extend(block)
        return i

    def handle_class(self, lines, i):
        header = lines[i].strip()
        match = re.search(r"class\s*\(([^)]*)\)", header)
        if not match:
            print("[!] Ошибка в заголовке класса:", header)
            return i + 1
        parts = [p.strip() for p in match.group(1).split(",")]
        name, params = parts[0], parts[1:]
        body = []
        i += 1
        while i < len(lines):
            token, val = tokenize_line(lines[i])
            if token == "class_end":
                break
            body.append(lines[i])
            i += 1

        class_code = [f"void {name}({', '.join(['char* ' + p for p in params])}) {{"]
        for line in body:
            token, value = tokenize_line(line)
            stmt = self.get_line_from_token(token, value, scope="class")
            class_code.append(stmt)
        class_code.append("}\n")
        self.funcs.extend(class_code)
        print(f"[+] Класс сгенерирован: {name}({', '.join(params)})")
        return i + 1

    def handle_class_call(self, call_line, scope="main"):
        name = call_line.split("(", 1)[0]
        args_str = call_line[len(name)+1:-1].strip()
        args = [f'"{a.strip().strip("\"")}"' for a in args_str.split(",")] if args_str else []
        stmt = f'{self.indent}{name}({", ".join(args)});'
        if scope == "main":
            self.main_body.append(stmt)
        else:
            self.funcs.append(stmt)

    def get_line_from_token(self, token, value, scope="main"):
        prefix = self.indent * (2 if scope == "class" else 1)
        if token == "print":
            return f'{prefix}printf({safe_c_expr(value)});'
        elif token == "delay":
            return f'{prefix}Sleep({value});'
        elif token == "assign":
            var, val = value
            return f'{prefix}int {var} = {safe_c_expr(val)};'
        elif token == "que":
            return f'{prefix}printf("Нажмите Enter для продолжения...");\n{prefix}getchar();'
        elif token == "bye":
            return f'{prefix}return 0;' if scope == "main" else f'{prefix}return;'
        elif token == "input":
            return f'{prefix}// input: {value}'
        elif token == "unknown" and "(" in value:
            return f'{prefix}{value};'
        return f'{prefix}// unknown: {value}'

    def write_c_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.output))
        print(f"[✓] C-код записан в {filename}")

    def build_exe(self, c_file, exe_file):
        res = os.system(f"tcc\\tcc \"{c_file}\" -o \"{exe_file}\"")
        if res == 0:
            print(f"[✓] Компиляция завершена: {exe_file}")
        else:
            print("[!] Ошибка компиляции.")
