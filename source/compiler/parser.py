import time
import sys
from lexer import tokenize_line
import os
import re

variables = {}
classes = {}

def safe_eval_condition(condition, local_vars):
    try:
        # __builtins__ None — чтобы ограничить доступ в eval для безопасности
        return eval(condition, {"__builtins__": None}, local_vars)
    except Exception as e:
        print(f"[!] Ошибка в условии if: {condition} -> {e}")
        return False

def run_script(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        token, value = tokenize_line(lines[i])

        if token == "print":
            try:
                print(eval(value, {}, variables))
            except:
                print(value)
        elif token == "que":
            input("Нажмите Enter для продолжения...")
        elif token == "delay":
            time.sleep(value / 1000)
        elif token == "bye":
            print("Завершение программы.")
            sys.exit()
        elif token == "assign":
            var, val = value
            variables[var] = eval(val, {}, variables)
        elif token == "input":
            exec(value, {}, variables)
        elif token == "import":
            if value.endswith(".tl"):
                run_script(value)
            else:
                run_script(os.path.join(value, "__init__.tl"))
        elif token == "class_start":
            i = parse_class(lines, i)
            continue
        elif token == "if_start":
            i = parse_if(lines, i, variables)
            continue
        elif token == "unknown":
            # Если строка — вызов функции, например hello("fff")
            if "(" in value and value.endswith(")"):
                call_name = value.split("(", 1)[0]
                args_str = value[len(call_name)+1:-1].strip()
                args = []
                if args_str:
                    args = [arg.strip().strip('"') for arg in args_str.split(",")]
                if call_name in classes:
                    call_class(call_name, args)
                else:
                    print(f"[!] Класс {call_name} не найден")
                    sys.exit()
            else:
                print(f"[?] Неизвестная строка: {value}")
        i += 1

def parse_class(lines, i):
    header = lines[i].strip()
    match = re.search(r"class\s*\(([^)]*)\)", header)
    if not match:
        print("[!] Ошибка разбора заголовка класса:", header)
        return i + 1
    params_str = match.group(1)
    parts = [p.strip() for p in params_str.split(",")]
    name = parts[0]
    params = parts[1:]
    body = []
    i += 1
    while i < len(lines):
        token, val = tokenize_line(lines[i])
        if token == "class_end":
            break
        body.append(lines[i].strip())
        i += 1
    classes[name] = {
        "params": params,
        "body": body
    }
    print(f"[+] Определён класс: {name} с параметрами {params}")
    return i + 1

def call_class(name, args):
    cls = classes[name]
    local_vars = {}
    for param, arg in zip(cls["params"], args):
        local_vars[param] = arg
    i = 0
    while i < len(cls["body"]):
        line = cls["body"][i]
        token, value = tokenize_line(line)
        if token == "print":
            try:
                print(eval(value, {}, local_vars))
            except:
                print(value)
        elif token == "que":
            input("Нажмите Enter для продолжения...")
        elif token == "delay":
            time.sleep(value / 1000)
        elif token == "assign":
            var, val = value
            local_vars[var] = eval(val, {}, local_vars)
        elif token == "input":
            exec(value, {}, local_vars)
        elif token == "if_start":
            i = parse_if(cls["body"], i, local_vars)
            continue
        else:
            print(f"[?] Неизвестная строка в классе {name}: {line}")
        i += 1

def parse_if(lines, i, local_vars):
    token, condition = tokenize_line(lines[i])
    i += 1  # следующий после if {
    body_lines = []
    depth = 1
    while i < len(lines) and depth > 0:
        t, v = tokenize_line(lines[i])
        if t == "if_start":
            depth += 1
        elif t == "block_end" or t == "class_end":
            depth -= 1
            if depth == 0:
                break
        body_lines.append(lines[i])
        i += 1

    cond_result = safe_eval_condition(condition, local_vars)

    if cond_result:
        j = 0
        while j < len(body_lines):
            line = body_lines[j]
            tkn, val = tokenize_line(line)
            if tkn == "print":
                try:
                    print(eval(val, {}, local_vars))
                except:
                    print(val)
            elif tkn == "que":
                input("Нажмите Enter для продолжения...")
            elif tkn == "delay":
                time.sleep(val / 1000)
            elif tkn == "assign":
                var, val_ = val
                local_vars[var] = eval(val_, {}, local_vars)
            elif tkn == "input":
                exec(val, {}, local_vars)
            elif tkn == "if_start":
                j = parse_if(body_lines, j, local_vars)
                continue
            else:
                print(f"[?] Неизвестная строка в if: {line}")
            j += 1

    return i