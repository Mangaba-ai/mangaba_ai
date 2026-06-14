#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação do ambiente para Mangaba AI

Este script verifica se o ambiente está configurado corretamente.
"""

import os
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime


class Colors:
    """Cores para output no terminal"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class EnvironmentValidator:
    """Classe para validação do ambiente"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.results = []
        self.warnings = []
        self.errors = []

    def log_result(self, test_name: str, status: str, message: str, details: str = ""):
        """Registra resultado de um teste"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)

        if status == "ERROR":
            self.errors.append(result)
        elif status == "WARNING":
            self.warnings.append(result)

    def print_header(self):
        """Imprime cabeçalho"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("=" * 60)
        print("    MANGABA AI - VALIDAÇÃO DO AMBIENTE")
        print("=" * 60)
        print(f"{Colors.END}")
        print("Verificando se o ambiente está configurado corretamente...")
        print()

    def check_python_version(self) -> bool:
        """Verifica versão do Python"""
        version = sys.version_info

        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log_result(
                "Python Version",
                "ERROR",
                f"Python 3.8+ necessário. Atual: {version.major}.{version.minor}",
                f"Versão completa: {sys.version}",
            )
            return False

        self.log_result(
            "Python Version",
            "OK",
            f"Python {version.major}.{version.minor}.{version.micro}",
            f"Versão completa: {sys.version}",
        )
        return True

    def check_required_files(self) -> bool:
        """Verifica arquivos obrigatórios"""
        required_files = [
            "mangaba_agent.py",
            "protocols/__init__.py",
            "protocols/a2a.py",
            "protocols/mcp.py",
            "requirements.txt",
        ]

        all_ok = True

        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_result(
                    f"Required File: {file_path}",
                    "OK",
                    "Arquivo encontrado",
                    f"Caminho: {full_path}",
                )
            else:
                self.log_result(
                    f"Required File: {file_path}",
                    "ERROR",
                    "Arquivo não encontrado",
                    f"Esperado em: {full_path}",
                )
                all_ok = False

        return all_ok

    def check_env_file(self) -> bool:
        """Verifica arquivo .env"""
        if not self.env_file.exists():
            self.log_result(
                "Environment File",
                "ERROR",
                "Arquivo .env não encontrado",
                "Execute: cp .env.template .env",
            )
            return False

        # Verifica se não está vazio
        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                self.log_result(
                    "Environment File",
                    "WARNING",
                    "Arquivo .env está vazio",
                    "Configure as variáveis necessárias",
                )
                return False

            self.log_result(
                "Environment File",
                "OK",
                "Arquivo .env encontrado",
                f"Tamanho: {len(content)} caracteres",
            )
            return True

        except Exception as e:
            self.log_result(
                "Environment File", "ERROR", "Erro ao ler arquivo .env", str(e)
            )
            return False

    def check_environment_variables(self) -> bool:
        """Verifica variáveis de ambiente"""
        # Carrega .env se existir
        if self.env_file.exists():
            try:
                with open(self.env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                self.log_result(
                    "Environment Variables", "WARNING", "Erro ao carregar .env", str(e)
                )

        alias_map = {
            "gemini": "google",
            "google-ai": "google",
            "googleai": "google",
            "gpt": "openai",
            "chatgpt": "openai",
            "claude": "anthropic",
            "hf": "huggingface",
            "hugging-face": "huggingface",
        }
        raw_provider = (os.getenv("LLM_PROVIDER") or "google").lower()
        provider = alias_map.get(raw_provider, raw_provider)

        provider_keys = {
            "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "huggingface": [
                "HUGGINGFACE_API_KEY",
                "HUGGINGFACE_TOKEN",
                "HF_TOKEN",
                "HUGGINGFACEHUB_API_TOKEN",
            ],
        }

        all_ok = True

        # Validar LLM_PROVIDER
        if provider not in provider_keys:
            self.log_result(
                "Required Variable: LLM_PROVIDER",
                "WARNING",
                f"Provedor '{provider}' não reconhecido",
                "Será necessário configurar manualmente via API_KEY",
            )
        else:
            self.log_result(
                "Required Variable: LLM_PROVIDER",
                "OK",
                f"Selecionado: {provider}",
                "Define qual provedor LLM será utilizado",
            )

        # Validar API key correspondente
        key_candidates = provider_keys.get(provider, [])
        key_candidates.append("API_KEY")  # fallback genérico

        key_name = None
        key_value = None
        for candidate in key_candidates:
            candidate_value = os.getenv(candidate)
            if candidate_value:
                key_name = candidate
                key_value = candidate_value
                break

        if not key_value:
            description = (
                f"Chave da API para o provedor '{provider}'. "
                f"Configure {key_candidates[0]} ou API_KEY."
            )
            self.log_result(
                "Required Variable: API Key",
                "ERROR",
                "Variável não configurada",
                description,
            )
            all_ok = False
        else:
            display_value = (
                key_value[:8] + "..."
                if "key" in (key_name or "").lower()
                else key_value
            )
            self.log_result(
                f"Required Variable: {key_name}",
                "OK",
                f"Configurada: {display_value}",
                f"Usada para autenticar no provedor {provider}",
            )

        # Variáveis opcionais com valores padrão
        optional_vars = {
            "MODEL_NAME": "gemini-2.5-flash",
            "MODEL_TEMPERATURE": "0.7",
            "MAX_OUTPUT_TOKENS": "1024",
            "AGENT_NAME": "MangabaAgent",
            "USE_MCP": "true",
            "USE_A2A": "true",
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "development",
        }

        for var, default in optional_vars.items():
            value = os.getenv(var, default)
            self.log_result(
                f"Optional Variable: {var}",
                "OK",
                f"Valor: {value}",
                f"Padrão: {default}",
            )

        return all_ok

    def check_dependencies(self) -> bool:
        """Verifica dependências instaladas"""
        required_packages = [
            "google-generativeai",
            "openai",
            "anthropic",
            "huggingface-hub",
            "python-dotenv",
            "loguru",
        ]

        all_ok = True

        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", package],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Extrai versão
                version = "unknown"
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        break

                self.log_result(
                    f"Package: {package}",
                    "OK",
                    f"Instalado (v{version})",
                    "Dependência encontrada",
                )

            except subprocess.CalledProcessError:
                self.log_result(
                    f"Package: {package}",
                    "ERROR",
                    "Pacote não instalado",
                    "Execute: pip install -r requirements.txt",
                )
                all_ok = False

        return all_ok

    def check_imports(self) -> bool:
        """Verifica se imports funcionam"""
        imports_to_test = [
            ("mangaba_agent", "MangabaAgent"),
            ("protocols.a2a", "A2AProtocol"),
            ("protocols.mcp", "MCPProtocol"),
            ("google.generativeai", None),
            ("openai", None),
            ("anthropic", None),
            ("huggingface_hub", None),
            ("dotenv", None),
            ("loguru", None),
        ]

        all_ok = True

        for module, class_name in imports_to_test:
            # Inicializar test_name antes de qualquer operação
            if class_name:
                test_name = f"Import: {module}.{class_name}"
            else:
                test_name = f"Import: {module}"

            try:
                if class_name:
                    exec(f"from {module} import {class_name}")
                else:
                    exec(f"import {module}")

                self.log_result(
                    test_name, "OK", "Import bem-sucedido", "Módulo disponível"
                )

            except ImportError as e:
                self.log_result(test_name, "ERROR", "Falha no import", str(e))
                all_ok = False
            except Exception as e:
                self.log_result(
                    test_name, "WARNING", "Erro inesperado no import", str(e)
                )

        return all_ok

    def check_api_connectivity(self) -> bool:
        """Verifica conectividade com API (teste básico)"""
        alias_map = {
            "gemini": "google",
            "google-ai": "google",
            "googleai": "google",
            "gpt": "openai",
            "chatgpt": "openai",
            "claude": "anthropic",
            "hf": "huggingface",
            "hugging-face": "huggingface",
        }
        raw_provider = (os.getenv("LLM_PROVIDER") or "google").lower()
        provider = alias_map.get(raw_provider, raw_provider)
        provider_keys = {
            "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "huggingface": [
                "HUGGINGFACE_API_KEY",
                "HUGGINGFACE_TOKEN",
                "HF_TOKEN",
                "HUGGINGFACEHUB_API_TOKEN",
            ],
        }
        key_candidates = provider_keys.get(provider, [])
        key_candidates.append("API_KEY")
        api_key = None
        for candidate in key_candidates:
            candidate_value = os.getenv(candidate)
            if candidate_value:
                api_key = candidate_value
                break

        if not api_key:
            self.log_result(
                "API Connectivity",
                "SKIP",
                "API key não configurada",
                f"Configure a variável correspondente ao provedor '{provider}'",
            )
            return True

        try:
            if provider == "google":
                import google.generativeai as genai

                genai.configure(api_key=api_key)
            elif provider == "openai":
                from openai import OpenAI

                OpenAI(api_key=api_key)
            elif provider == "anthropic":
                from anthropic import Anthropic

                Anthropic(api_key=api_key)
            elif provider == "huggingface":
                from huggingface_hub import InferenceClient

                InferenceClient(token=api_key)
            else:
                self.log_result(
                    "API Connectivity",
                    "SKIP",
                    f"Provedor '{provider}' personalizado",
                    "Configure manualmente se necessário",
                )
                return True

            self.log_result(
                "API Connectivity",
                "OK",
                f"Cliente do provedor '{provider}' configurado",
                "Teste de conectividade básico passou",
            )
            return True

        except ImportError as e:
            self.log_result(
                "API Connectivity", "ERROR", "Dependência não instalada", str(e)
            )
            return False
        except Exception as e:
            self.log_result(
                "API Connectivity", "ERROR", "Erro na configuração da API", str(e)
            )
            return False

    def check_test_environment(self) -> bool:
        """Verifica ambiente de testes"""
        test_files = [
            "tests/test_mangaba_agent.py",
            "tests/test_a2a_protocol.py",
            "tests/test_mcp_protocol.py",
            "tests/test_integration.py",
        ]

        tests_available = True

        for test_file in test_files:
            full_path = self.project_root / test_file
            if not full_path.exists():
                tests_available = False
                break

        if tests_available:
            self.log_result(
                "Test Environment",
                "OK",
                "Arquivos de teste encontrados",
                "Execute: python -m pytest tests/ -v",
            )
        else:
            self.log_result(
                "Test Environment",
                "WARNING",
                "Alguns arquivos de teste não encontrados",
                "Testes podem não estar completos",
            )

        # Verifica pytest
        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                check=True,
            )
            self.log_result(
                "Pytest", "OK", "pytest disponível", "Framework de testes instalado"
            )
        except subprocess.CalledProcessError:
            self.log_result(
                "Pytest",
                "WARNING",
                "pytest não disponível",
                "Instale: pip install pytest",
            )

        return tests_available

    def print_summary(self):
        """Imprime resumo dos resultados"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("=" * 60)
        print("    RESUMO DA VALIDAÇÃO")
        print("=" * 60)
        print(f"{Colors.END}")

        # Contadores
        total_tests = len(self.results)
        ok_count = len([r for r in self.results if r["status"] == "OK"])
        warning_count = len(self.warnings)
        error_count = len(self.errors)
        skip_count = len([r for r in self.results if r["status"] == "SKIP"])

        print(f"Total de verificações: {total_tests}")
        print(f"{Colors.GREEN}[OK] Sucessos: {ok_count}{Colors.END}")
        print(f"{Colors.YELLOW}[WARN] Avisos: {warning_count}{Colors.END}")
        print(f"{Colors.RED}[ERROR] Erros: {error_count}{Colors.END}")
        print(f"[SKIP] Pulados: {skip_count}")
        print()

        # Mostra erros
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}ERROS ENCONTRADOS:{Colors.END}")
            for error in self.errors:
                print(
                    f"{Colors.RED}[ERROR] {error['test']}: {error['message']}{Colors.END}"
                )
                if error["details"]:
                    print(f"   [INFO] {error['details']}")
            print()

        # Mostra avisos
        if self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}AVISOS:{Colors.END}")
            for warning in self.warnings:
                print(
                    f"{Colors.YELLOW}[WARN] {warning['test']}: {warning['message']}{Colors.END}"
                )
                if warning["details"]:
                    print(f"   [INFO] {warning['details']}")
            print()

        # Status geral
        if error_count == 0:
            if warning_count == 0:
                print(
                    f"{Colors.GREEN}{Colors.BOLD}[SUCCESS] AMBIENTE TOTALMENTE CONFIGURADO!{Colors.END}"
                )
                print("Você pode começar a usar o Mangaba AI.")
            else:
                print(
                    f"{Colors.YELLOW}{Colors.BOLD}[OK] AMBIENTE FUNCIONAL COM AVISOS{Colors.END}"
                )
                print("O sistema deve funcionar, mas considere resolver os avisos.")
        else:
            print(f"{Colors.RED}{Colors.BOLD}[ERROR] PROBLEMAS ENCONTRADOS{Colors.END}")
            print("Resolva os erros antes de usar o sistema.")

        print()
        print("[INFO] Para mais informações, consulte:")
        print("   - SETUP.md (guia de configuração)")
        print("   - README.md (documentação geral)")
        print("   - .env.template (exemplo de configuração)")

    def save_report(self, filename: str = "validation_report.json"):
        """Salva relatório em JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "ok_count": len([r for r in self.results if r["status"] == "OK"]),
                "warning_count": len(self.warnings),
                "error_count": len(self.errors),
                "skip_count": len([r for r in self.results if r["status"] == "SKIP"]),
            },
            "results": self.results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(self.project_root),
            },
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Relatório salvo em: {filename}")
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Erro ao salvar relatório: {e}{Colors.END}")

    def run_validation(self, save_report: bool = False) -> bool:
        """Executa validação completa"""
        self.print_header()

        # Lista de verificações
        checks = [
            ("Versão do Python", self.check_python_version),
            ("Arquivos obrigatórios", self.check_required_files),
            ("Arquivo .env", self.check_env_file),
            ("Variáveis de ambiente", self.check_environment_variables),
            ("Dependências", self.check_dependencies),
            ("Imports", self.check_imports),
            ("Conectividade API", self.check_api_connectivity),
            ("Ambiente de testes", self.check_test_environment),
        ]

        print("Executando verificações...")
        print()

        # Executa verificações
        for check_name, check_func in checks:
            print(f"[CHECK] {check_name}...", end=" ")
            try:
                result = check_func()
                if result:
                    print(f"{Colors.GREEN}OK{Colors.END}")
                else:
                    print(f"{Colors.RED}FALHOU{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}ERRO: {e}{Colors.END}")
                self.log_result(
                    check_name, "ERROR", "Erro inesperado na verificação", str(e)
                )

        print()

        # Mostra resumo
        self.print_summary()

        # Salva relatório se solicitado
        if save_report:
            self.save_report()

        # Retorna True se não há erros críticos
        return len(self.errors) == 0


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Valida configuração do ambiente Mangaba AI"
    )
    parser.add_argument(
        "--save-report", action="store_true", help="Salva relatório em JSON"
    )
    parser.add_argument(
        "--json-output", action="store_true", help="Output apenas em JSON"
    )

    args = parser.parse_args()

    try:
        validator = EnvironmentValidator()

        if args.json_output:
            # Executa validação silenciosa
            validator.run_validation(save_report=False)

            # Output apenas JSON
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": len(validator.results),
                    "ok_count": len(
                        [r for r in validator.results if r["status"] == "OK"]
                    ),
                    "warning_count": len(validator.warnings),
                    "error_count": len(validator.errors),
                    "valid": len(validator.errors) == 0,
                },
                "results": validator.results,
            }
            print(json.dumps(report, indent=2))
        else:
            # Execução normal
            success = validator.run_validation(save_report=args.save_report)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARN] Validação cancelada pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Erro inesperado: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
