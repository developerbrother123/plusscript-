import re
import sys
import os
import threading
import asyncio
import time
import tkinter as tk
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import mysql.connector
import psycopg2
import PIL.Image
import PIL.ImageDraw
import numpy as np
import socket
import subprocess
import hashlib
import uuid
import json
import ctypes
import base64
import wave
import boto3
import paho.mqtt.client as mqtt
from web3 import Web3
import ast
import multiprocessing
import urllib.request  # For downloading packages

# Global state
variables = {}
functions = {}
classes = {}
modules = {}
event_loop = asyncio.get_event_loop()
game_window = None
game_canvas = None
api_keys = {}
compiled_cache = {}
types = {}
PACKAGE_DIR = "./plusscript/module"
PACKAGE_DB = "packages.json"

# Ensure package directory and DB exist
if not os.path.exists(PACKAGE_DIR):
    os.makedirs(PACKAGE_DIR)
if not os.path.exists(PACKAGE_DB):
    with open(PACKAGE_DB, 'w') as f:
        json.dump({}, f)

# Token definitions (only showing new/changed parts)
TOKENS = [
    # ... (previous tokens unchanged)
    (r'pkg\s+(\w+)\s+"([^"]+)"', 'PKG'),
    # ... (rest unchanged)
]

# Built-in functions (only showing new/changed parts)
BUILTINS = {
    # ... (previous builtins unchanged)
    'pkg_install': lambda name, source: install_package(name, source),
    'pkg_list': lambda: list_packages(),
}

def install_package(name, source):
    """Install a package from a source (URL or local path)."""
    pkg_path = os.path.join(PACKAGE_DIR, f"{name}.ps")
    
    # Download or copy package
    if source.startswith("http://") or source.startswith("https://"):
        urllib.request.urlretrieve(source, pkg_path)
    elif os.path.exists(source):
        with open(source, 'r') as src, open(pkg_path, 'w') as dst:
            dst.write(src.read())
    else:
        raise ValueError(f"Invalid package source: {source}")
    
    # Parse package for metadata and dependencies
    with open(pkg_path, 'r') as f:
        code = f.read()
        metadata = {}
        for line in code.split('\n'):
            if line.startswith('# pkg_name:'):
                metadata['name'] = line.split(':')[1].strip()
            elif line.startswith('# pkg_version:'):
                metadata['version'] = line.split(':')[1].strip()
            elif line.startswith('# pkg_deps:'):
                metadata['deps'] = [d.strip() for d in line.split(':')[1].split(',') if d.strip()]
    
    # Update package database
    with open(PACKAGE_DB, 'r') as f:
        pkg_db = json.load(f)
    pkg_db[name] = {
        'source': source,
        'version': metadata.get('version', '1.0.0'),
        'deps': metadata.get('deps', []),
        'path': pkg_path
    }
    with open(PACKAGE_DB, 'w') as f:
        json.dump(pkg_db, f, indent=2)
    
    # Install dependencies
    for dep in metadata.get('deps', []):
        if dep not in pkg_db:
            # Placeholder: assume deps are in same source dir or repo
            install_package(dep, source.replace(name, dep))
    
    return f"Installed {name}"

def list_packages():
    """Return a list of installed packages."""
    with open(PACKAGE_DB, 'r') as f:
        pkg_db = json.load(f)
    return list(pkg_db.keys())

# Expression parser (unchanged for brevity)
class ExprParser:
    def __init__(self, expr, local_vars):
        if isinstance(expr, ast.AST):
            self.compiled = expr
            self.local_vars = local_vars
        else:
            self.tokens = re.findall(r'[\w.]+|\[.*?\]|\{.*?\}|\S', expr)
            self.pos = 0
            self.local_vars = local_vars

    def parse(self):
        if hasattr(self, 'compiled'):
            return self.eval_ast(self.compiled)
        return self.expr()

    def eval_ast(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Name):
            return self.local_vars[node.id]
        elif isinstance(node, ast.BinOp):
            left = self.eval_ast(node.left)
            right = self.eval_ast(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
        raise ValueError("Unsupported AST node")

    def expr(self):
        left = self.term()
        while self.pos < len(self.tokens) and self.tokens[self.pos] in ('+', '-', '==', '>', '<', '>=', '<='):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.term()
            if op == '+': left = left + right if isinstance(left, str) else left + right
            elif op == '-': left = left - right
            elif op == '==': left = left == right
            elif op == '>': left = left > right
            elif op == '<': left = left < right
            elif op == '>=': left = left >= right
            elif op == '<=': left = left <= right
        return left

    def term(self):
        left = self.factor()
        while self.pos < len(self.tokens) and self.tokens[self.pos] in ('*', '/'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.factor()
            if op == '*': left = left * right
            elif op == '/': left = left / right
        return left

    def factor(self):
        token = self.tokens[self.pos] if self.pos < len(self.tokens) else ''
        self.pos += 1
        if token.isdigit(): return float(token)
        elif token.startswith('"') and token.endswith('"'): return token[1:-1]
        elif token.startswith('['): return [self.parse_item(x.strip()) for x in token[1:-1].split(',') if x.strip()]
        elif token.startswith('{'):
            items = {}
            for pair in token[1:-1].split(','):
                if ':' in pair:
                    k, v = pair.split(':')
                    items[self.parse_item(k.strip())] = self.parse_item(v.strip())
            return items
        elif token in self.local_vars:
            if token in types and not isinstance(self.local_vars[token], eval(types[token])):
                raise TypeError(f"{token} must be {types[token]}")
            return self.local_vars[token]
        elif '.' in token:
            obj, attr = token.split('.')
            return self.local_vars[obj][attr]
        elif token.endswith(']'):
            var, idx = token.split('[')
            idx = self.parse_item(idx[:-1])
            return self.local_vars[var][idx]
        raise ValueError(f"Invalid token: {token}")

    def parse_item(self, item):
        return ExprParser(item, self.local_vars).parse()

def evaluate(expr, local_vars=None):
    if local_vars is None:
        local_vars = variables
    if expr in BUILTINS:
        return BUILTINS[expr]
    return ExprParser(expr, local_vars).parse()

def create_instance(class_name):
    cls = classes[class_name]
    instance = {'__class__': class_name}
    for attr, val in cls['attributes'].items():
        instance[attr] = val
    return instance

class PlusScriptHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path in variables.get('api_endpoints', {}):
            key = self.headers.get('API-Key')
            if key in api_keys:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = variables['api_endpoints'][path]
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Invalid API Key")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            response = variables.get('server_response', "Hello from PlusScript!")
            self.wfile.write(response.encode())

def run(tokens, local_vars=None, return_early=False):
    global game_window, game_canvas
    if local_vars is None:
        local_vars = variables.copy()
    
    tokens = compile_code(tokens)
    
    i = 0
    return_value = None
    while i < len(tokens):
        token_type, args, line_num = tokens[i]
        
        if token_type == 'SET':
            target, expr = args
            value = evaluate(expr, local_vars)
            if target in types and not isinstance(value, eval(types[target])):
                raise TypeError(f"{target} must be {types[target]}")
            if '.' in target:
                obj, attr = target.split('.')
                local_vars[obj][attr] = value
            else:
                local_vars[target] = value
        
        elif token_type == 'SHOW':
            print(evaluate(args[0], local_vars))
        
        elif token_type in ('FUNC', 'METHOD', 'ASYNC_FUNC'):
            func_name, params = args
            param_list = [p.strip() for p in params.split() if p.strip()]
            func_body = []
            i += 1
            while i < len(tokens) and tokens[i][0] != 'END':
                func_body.append(tokens[i])
                i += 1
            if token_type == 'FUNC':
                functions[func_name] = (param_list, func_body, False)
            elif token_type == 'METHOD':
                cls_name = list(classes.keys())[-1]
                classes[cls_name]['methods'][func_name] = (param_list, func_body, False)
            else:
                functions[func_name] = (param_list, func_body, True)
        
        elif token_type == 'CALL':
            name, call_args = args
            if name in functions:
                param_list, func_body, is_async = functions[name]
                args = [evaluate(a.strip(), local_vars) for a in call_args.split(',') if a.strip()]
                local_scope = local_vars.copy()
                for param, arg in zip(param_list, args):
                    local_scope[param] = arg
                if is_async:
                    async def wrapper():
                        return run(func_body, local_scope, True)
                    return_value = asyncio.run(wrapper())
                else:
                    return_value = run(func_body, local_scope, True)
            elif name in BUILTINS:
                args = [evaluate(a.strip(), local_vars) for a in call_args.split(',') if a.strip()]
                return_value = BUILTINS[name](*args)
            elif name in classes:
                local_vars[name] = create_instance(name)
            elif '.' in name:
                obj, method = name.split('.')
                param_list, func_body, _ = classes[local_vars[obj]['__class__']]['methods'][method]
                args = [evaluate(a.strip(), local_vars) for a in call_args.split(',') if a.strip()]
                local_scope = local_vars.copy()
                local_scope['self'] = local_vars[obj]
                for param, arg in zip(param_list, args):
                    local_scope[param] = arg
                return_value = run(func_body, local_scope, True)
        
        elif token_type == 'PKG':
            name, source = args
            local_vars[name] = BUILTINS['pkg_install'](name, source)
            # Load package into modules
            pkg_path = os.path.join(PACKAGE_DIR, f"{name}.ps")
            with open(pkg_path, 'r') as f:
                modules[name] = tokenize(f.read())
            run(modules[name], variables)
        
        elif token_type == 'IMPORT':
            filename = args[0]
            if filename in BUILTINS['pkg_list']():
                pkg_path = os.path.join(PACKAGE_DIR, f"{filename}.ps")
                if pkg_path not in modules:
                    with open(pkg_path, 'r') as f:
                        modules[pkg_path] = tokenize(f.read())
                    run(modules[pkg_path], variables)
            elif filename not in modules:
                with open(filename, 'r') as f:
                    modules[filename] = tokenize(f.read())
                run(modules[filename], variables)
        
        elif token_type == 'FROM_IMPORT':
            filename, imports = args
            if filename in BUILTINS['pkg_list']():
                pkg_path = os.path.join(PACKAGE_DIR, f"{filename}.ps")
                if pkg_path not in modules:
                    with open(pkg_path, 'r') as f:
                        modules[pkg_path] = tokenize(f.read())
                    run(modules[pkg_path], variables)
            elif filename not in modules:
                with open(filename, 'r') as f:
                    modules[filename] = tokenize(f.read())
                run(modules[filename], variables)
            for imp in imports.split(','):
                imp = imp.strip()
                if imp in functions:
                    local_vars[imp] = functions[imp]
                elif imp in variables:
                    local_vars[imp] = variables[imp]
        
        # Other token types unchanged for brevity
        
        i += 1
    return return_value

def compile_code(tokens):
    key = str(tokens)
    if key in compiled_cache:
        return compiled_cache[key]
    compiled = []
    for token in tokens:
        token_type, args, line_num = token
        if token_type == 'EXPRESSION':
            compiled.append((token_type, ast.parse(args[0]).body[0].value, line_num))
        else:
            compiled.append(token)
    compiled_cache[key] = compiled
    return compiled

def tokenize(code):
    tokens = []
    lines = code.split('\n')
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        matched = False
        for pattern, token_type in TOKENS:
            match = re.match(pattern, line)
            if match:
                tokens.append((token_type, match.groups(), line_num))
                matched = True
                break
        if not matched:
            raise SyntaxError(f"Invalid syntax at line {line_num}: {line}")
    return tokens

def repl():
    print("PlusScript REPL - The Hyper-Language with Package Manager (type 'exit' to quit)")
    code = ""
    while True:
        line = input(">>> " if not code else "... ")
        if line == 'exit':
            break
        code += line + "\n"
        try:
            if not line.strip() or line.strip().endswith(':') or code.count('+func') > code.count('+end'):
                continue
            tokens = tokenize(code)
            run(tokens)
            code = ""
        except Exception as e:
            print(f"Error: {e}")
            code = ""

def execute_file(filename):
    with open(filename, 'r') as f:
        code = f.read()
    tokens = tokenize(code)
    run(tokens)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_file(sys.argv[1])
    else:
        repl()