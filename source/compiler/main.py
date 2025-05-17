# main.py

import sys
import os
from parser import run_script
from compiler import CCompiler
from os import remove

def print_help():
    print("""
Использование:
  tlc -c <входной_файл> [-o <выходной_файл>]    # Компиляция
  tlc -i <входной_файл>                         # Интерпретация
  tlc -h                                        # Справка
  tlc                                           # Интерактивный режим
""")

def compile_file(input_file, output_file):
    compiler = CCompiler()
    compiler.compile_script(input_file)
    compiler.write_c_file("out.c")
    compiler.build_exe("out.c", output_file)
    remove("out.c")
    print(f"Компиляция завершена. Скомпилированный файл: {output_file}")

def get_output_name(input_file):
    base, _ = os.path.splitext(input_file)
    return base + ".exe"

def main():
    args = sys.argv[1:]

    if not args:
        # Интерактивный режим
        while True:
            choice = input("1: Интерпретировать. 2: Компилировать. 1/2: ")
            if choice == "1":
                filename = input("Введите название файла для интерпретации: ")
                run_script(filename)
                break
            elif choice == "2":
                inputF = input("Введите название файла для компиляции: ")
                outF = input("Введите название для файла на выход: ")
                compile_file(inputF, outF)
                break
            else:
                print("Неверный выбор.")
    elif args[0] == "-h":
        print_help()
    elif args[0] == "-i" and len(args) >= 2:
        run_script(args[1])
    elif args[0] == "-c" and len(args) >= 2:
        inputF = args[1]
        if "-o" in args:
            idx = args.index("-o")
            if idx + 1 < len(args):
                outputF = args[idx + 1]
            else:
                print("Ошибка: не указано имя выходного файла после -o.")
                return
        else:
            outputF = get_output_name(inputF)
        compile_file(inputF, outputF)
    else:
        print("Неверные аргументы. Используйте -h для справки.")

if __name__ == "__main__":
    main()
