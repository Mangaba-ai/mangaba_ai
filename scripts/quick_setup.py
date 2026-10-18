#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuração rápida para Mangaba AI

Este script automatiza todo o processo de setup inicial.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
import json
import re
from datetime import datetime


class Colors:
    """Cores para output no terminal"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class QuickSetup:
    """Classe para configuração rápida do projeto"""
    
    def __init__(self):
        # scripts/quick_setup.py → raiz do repositório, de onde quer que seja chamado (#17)
        self.project_root = Path(__file__).resolve().parent.parent
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / '.env.example'
        self.venv_path = self.project_root / 'venv'
        self.steps_completed = []
        self.errors = []
    
    def log_step(self, step: str, success: bool, message: str = ""):
        """Registra resultado de um passo"""
        if success:
            self.steps_completed.append(step)
            print(f"{Colors.GREEN}[OK] {step}{Colors.END}")
            if message:
                print(f"   {message}")
        else:
            self.errors.append((step, message))
            print(f"{Colors.RED}[ERROR] {step}{Colors.END}")
            if message:
                print(f"   {Colors.RED}{message}{Colors.END}")
    
    def print_header(self):
        """Imprime cabeçalho"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("="*60)
        print("    MANGABA AI - CONFIGURAÇÃO RÁPIDA")
        print("="*60)
        print(f"{Colors.END}")
        print("Este script irá configurar automaticamente o ambiente.")
        print("Pressione Ctrl+C a qualquer momento para cancelar.")
        print()
    
    def check_python_version(self) -> bool:
        """Verifica versão do Python"""
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.log_step(
                "Verificar Python",
                False,
                f"Python 3.10+ necessário. Atual: {version.major}.{version.minor}"
            )
            return False
        
        self.log_step(
            "Verificar Python",
            True,
            f"Python {version.major}.{version.minor}.{version.micro} OK"
        )
        return True
    
    def create_virtual_environment(self) -> bool:
        """Cria ambiente virtual"""
        if self.venv_path.exists():
            self.log_step(
                "Ambiente Virtual",
                True,
                "Ambiente virtual já existe"
            )
            return True
        
        try:
            print(f"[INFO] Criando ambiente virtual em {self.venv_path}...")
            subprocess.run(
                [sys.executable, '-m', 'venv', str(self.venv_path)],
                check=True,
                capture_output=True
            )
            
            self.log_step(
                "Criar Ambiente Virtual",
                True,
                f"Criado em {self.venv_path}"
            )
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_step(
                "Criar Ambiente Virtual",
                False,
                f"Erro: {e}"
            )
            return False
    
    def get_venv_python(self) -> Optional[str]:
        """Retorna caminho do Python no venv"""
        if sys.platform == "win32":
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:
            python_path = self.venv_path / "bin" / "python"
        
        return str(python_path) if python_path.exists() else None
    
    def get_venv_pip(self) -> Optional[str]:
        """Retorna caminho do pip no venv"""
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = self.venv_path / "bin" / "pip"
        
        return str(pip_path) if pip_path.exists() else None
    
    def upgrade_pip(self) -> bool:
        """Atualiza pip no ambiente virtual"""
        python_path = self.get_venv_python()
        if not python_path:
            self.log_step(
                "Atualizar pip",
                False,
                "Python do ambiente virtual não encontrado"
            )
            return False
        
        try:
            print("[INFO] Atualizando pip...")
            # `python -m pip`: o executável pip não consegue se substituir
            # enquanto roda (falha no Windows e no Python 3.13) (#15)
            subprocess.run(
                [python_path, '-m', 'pip', 'install', '--upgrade', 'pip'],
                check=True,
                capture_output=True
            )
            
            self.log_step(
                "Atualizar pip",
                True,
                "pip atualizado com sucesso"
            )
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_step(
                "Atualizar pip",
                False,
                f"Erro: {e}"
            )
            return False
    
    def install_dependencies(self) -> bool:
        """Instala o Mangaba em modo editável com Gemini e dependências de teste"""
        python_path = self.get_venv_python()
        if not python_path:
            self.log_step(
                "Instalar Dependências",
                False,
                "Python do ambiente virtual não encontrado"
            )
            return False
        
        # Caminho absoluto: `-e .` dentro de requirements.txt é resolvido a
        # partir do diretório atual, não do arquivo
        target = f"{self.project_root}[google,test]"
        try:
            print("[INFO] Instalando mangaba[google,test]...")
            subprocess.run(
                [python_path, '-m', 'pip', 'install', '-e', target],
                check=True,
                capture_output=True,
                cwd=str(self.project_root),
            )
            self.log_step(
                "Instalar Dependências",
                True,
                "mangaba instalado em modo editável com [google,test]"
            )
            return True
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or b"").decode(errors="replace").strip().splitlines()[-1:] or [str(e)]
            self.log_step(
                "Instalar Dependências",
                False,
                f"Erro: {detail[0]}"
            )
            return False
    
    def setup_env_file(self) -> bool:
        """Configura arquivo .env"""
        # Se .env já existe, pergunta se quer sobrescrever
        if self.env_file.exists():
            print(f"\n{Colors.YELLOW}[WARN] Arquivo .env já existe.{Colors.END}")
            response = input("Deseja sobrescrever? (s/N): ").strip().lower()
            
            if response not in ['s', 'sim', 'y', 'yes']:
                self.log_step(
                    "Configurar .env",
                    True,
                    "Mantendo arquivo .env existente"
                )
                return True
        
        # Verifica se template existe
        if not self.env_template.exists():
            self.log_step(
                "Configurar .env",
                False,
                ".env.example não encontrado"
            )
            return False
        
        try:
            # Copia template
            shutil.copy2(self.env_template, self.env_file)
            
            # Solicita configurações básicas
            print(f"\n{Colors.BLUE}[CONFIG] Configuração do arquivo .env:{Colors.END}")
            print("Pressione Enter para usar valores padrão.")
            print()
            
            # Google API Key (obrigatório)
            while True:
                api_key = input("🔑 Google API Key (obrigatório): ").strip()
                if api_key:
                    break
                print(f"{Colors.RED}[ERROR] API Key é obrigatória!{Colors.END}")
                print("[INFO] Obtenha em: https://makersuite.google.com/app/apikey")
            
            # Outras configurações opcionais
            model_name = input("🤖 Nome do modelo [gemini-2.5-flash]: ").strip() or "gemini-2.5-flash"
            agent_name = input("👤 Nome do agente [MangabaAgent]: ").strip() or "MangabaAgent"
            log_level = input("📊 Nível de log [INFO]: ").strip() or "INFO"
            
            # Atualiza arquivo .env
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Preenche as chaves do .env.example (linhas KEY=valor)
            values = {
                'GOOGLE_API_KEY': api_key,
                'MODEL_NAME': model_name,
                'AGENT_NAME': agent_name,
                'LOG_LEVEL': log_level,
            }
            for key, value in values.items():
                content, count = re.subn(
                    rf'^{key}=.*$', lambda _m, k=key, v=value: f'{k}={v}', content, flags=re.MULTILINE
                )
                if not count:
                    content += f'\n{key}={value}\n'
            
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_step(
                "Configurar .env",
                True,
                "Arquivo .env configurado com sucesso"
            )
            return True
            
        except Exception as e:
            self.log_step(
                "Configurar .env",
                False,
                f"Erro: {e}"
            )
            return False
    
    def test_installation(self) -> bool:
        """Testa instalação básica"""
        python_path = self.get_venv_python()
        if not python_path:
            self.log_step(
                "Testar Instalação",
                False,
                "Python do venv não encontrado"
            )
            return False
        
        # Script de teste básico
        test_script = '''
import sys
sys.path.insert(0, ".")

try:
    # Testa imports do framework
    from mangaba import Agent, Crew, Task, tool
    from mangaba.flows import Flow
    
    # Testa dependências
    import google.generativeai as genai
    from dotenv import load_dotenv
    
    print("SUCCESS: Todos os imports funcionaram")
    
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''
        
        try:
            print("[INFO] Testando instalação...")
            result = subprocess.run(
                [python_path, '-c', test_script],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                self.log_step(
                    "Testar Instalação",
                    True,
                    "Todos os imports funcionaram"
                )
                return True
            else:
                error_msg = result.stderr or result.stdout or "Erro desconhecido"
                self.log_step(
                    "Testar Instalação",
                    False,
                    f"Falha nos imports: {error_msg}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.log_step(
                "Testar Instalação",
                False,
                "Timeout no teste de instalação"
            )
            return False
        except Exception as e:
            self.log_step(
                "Testar Instalação",
                False,
                f"Erro: {e}"
            )
            return False
    
    def run_validation(self) -> bool:
        """Executa validação final"""
        python_path = self.get_venv_python()
        if not python_path:
            self.log_step(
                "Validação Final",
                False,
                "Python do venv não encontrado"
            )
            return False
        
        validate_script = self.project_root / "scripts" / "validate_env.py"
        if not validate_script.exists():
            self.log_step(
                "Validação Final",
                False,
                "Script de validação não encontrado"
            )
            return False
        
        try:
            print("[INFO] Executando validação final...")
            result = subprocess.run(
                [python_path, str(validate_script), '--json-output'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout.strip():
                # stdout traz só o JSON; os logs da validação vão para stderr (#18)
                try:
                    validation_result = json.loads(result.stdout)
                    if validation_result.get('summary', {}).get('valid', False):
                        self.log_step(
                            "Validação Final",
                            True,
                            "Ambiente validado com sucesso"
                        )
                        return True
                    else:
                        error_count = validation_result.get('summary', {}).get('error_count', 0)
                        self.log_step(
                            "Validação Final",
                            False,
                            f"Validação falhou com {error_count} erros"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_step(
                        "Validação Final",
                        False,
                        "Erro ao interpretar resultado da validação"
                    )
                    return False
            else:
                self.log_step(
                    "Validação Final",
                    False,
                    f"Validação falhou: {result.stderr}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.log_step(
                "Validação Final",
                False,
                "Timeout na validação"
            )
            return False
        except Exception as e:
            self.log_step(
                "Validação Final",
                False,
                f"Erro: {e}"
            )
            return False
    
    def print_summary(self):
        """Imprime resumo final"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}")
        print("="*60)
        print("    RESUMO DA CONFIGURAÇÃO")
        print("="*60)
        print(f"{Colors.END}")
        
        print(f"[OK] Passos concluídos: {len(self.steps_completed)}")
        print(f"[ERROR] Erros encontrados: {len(self.errors)}")
        print()
        
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}ERROS:{Colors.END}")
            for step, error in self.errors:
                print(f"{Colors.RED}[ERROR] {step}: {error}{Colors.END}")
            print()
        
        if len(self.errors) == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS] CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!{Colors.END}")
            print()
            print("[INFO] Próximos passos:")
            print("   1. Ative o ambiente virtual:")
            if sys.platform == "win32":
                print(f"      {self.venv_path}\\Scripts\\activate")
            else:
                print(f"      source {self.venv_path}/bin/activate")
            print("   2. Execute os testes:")
            print("      python -m pytest tests/ -v")
            print("   3. Teste o agente:")
            print("      python examples/quickstart.py")
            print()
            print("[INFO] Documentação:")
            print("   - README.md (visão geral)")
            print("   - docs/SETUP.md (configuração detalhada)")
            print("   - examples/ (exemplos de uso)")
        else:
            print(f"{Colors.RED}{Colors.BOLD}[ERROR] CONFIGURAÇÃO INCOMPLETA{Colors.END}")
            print("Resolva os erros acima e execute novamente.")
            print()
            print("[INFO] Para configuração manual, consulte docs/SETUP.md")
    
    def run_setup(self, skip_validation: bool = False) -> bool:
        """Executa configuração completa"""
        self.print_header()
        
        # Lista de passos
        steps = [
            ("Verificar Python", self.check_python_version),
            ("Criar ambiente virtual", self.create_virtual_environment),
            ("Atualizar pip", self.upgrade_pip),
            ("Instalar dependências", self.install_dependencies),
            ("Configurar .env", self.setup_env_file),
            ("Testar instalação", self.test_installation)
        ]
        
        if not skip_validation:
            steps.append(("Validação final", self.run_validation))
        
        print("[INFO] Iniciando configuração automática...")
        print()
        
        # Executa passos
        for step_name, step_func in steps:
            try:
                print(f"[INFO] {step_name}...")
                success = step_func()
                
                if not success and step_name in ["Verificar Python", "Criar ambiente virtual"]:
                    print(f"{Colors.RED}[ERROR] Erro crítico em '{step_name}'. Abortando.{Colors.END}")
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[WARN] Configuração cancelada pelo usuário{Colors.END}")
                return False
            except Exception as e:
                self.log_step(
                    step_name,
                    False,
                    f"Erro inesperado: {e}"
                )
        
        print()
        self.print_summary()
        
        return len(self.errors) == 0


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Configuração rápida do Mangaba AI"
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Pula validação final'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Modo não-interativo (usa valores padrão)'
    )
    
    args = parser.parse_args()
    
    try:
        setup = QuickSetup()
        
        if args.non_interactive:
            # TODO: Implementar modo não-interativo
            print(f"{Colors.YELLOW}[WARN] Modo não-interativo ainda não implementado{Colors.END}")
            print("Use o modo interativo por enquanto.")
            return
        
        success = setup.run_setup(skip_validation=args.skip_validation)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARN] Configuração cancelada pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Erro inesperado: {e}{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()