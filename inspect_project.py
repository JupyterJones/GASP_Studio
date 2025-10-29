#!/usr/bin/env python3
import ast
import os
import datetime
from icecream import ic

APP_FILE = "app.py"
OUTPUT_FILE = "Inspection.txt"

def extract_routes_and_templates(filename):
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    routes = []
    templates = []

    for node in ast.walk(tree):
        # Flask route decorators
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "route":
                        if len(decorator.args) > 0 and isinstance(decorator.args[0], ast.Constant):
                            route_path = decorator.args[0].value
                            routes.append((route_path, node.name))

        # render_template() calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "render_template":
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    templates.append(node.args[0].value)

    return routes, templates


def generate_report(routes, templates):
    report_lines = []
    report_lines.append(f"=== 🧭 ROUTES FOUND ===")
    for path, func in routes:
        report_lines.append(f"  {path:<30} -> {func}")

    report_lines.append("\n=== 🧩 HTML Templates Used ===")
    for tpl in templates:
        report_lines.append(f"  {tpl}")

    report_lines.append("\n=== 📁 Template Files Present ===")
    if os.path.exists("templates"):
        for file in sorted(os.listdir("templates")):
            if file.endswith(".html"):
                report_lines.append(f"  {file}")
    else:
        report_lines.append("  No 'templates' directory found!")

    return "\n".join(report_lines)


def main():
    if not os.path.exists(APP_FILE):
        ic(f"Error: {APP_FILE} not found in current directory.")
        return

    ic(f"Inspecting {APP_FILE} ...")

    routes, templates = extract_routes_and_templates(APP_FILE)
    report = generate_report(routes, templates)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"📋 Flask Project Inspection Report\nGenerated: {timestamp}\n{'='*50}\n\n"

    full_report = header + report + "\n\n✅ Inspection complete.\n"

    print(full_report)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_report)

    ic(f"Report saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
