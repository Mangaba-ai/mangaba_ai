#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuração automática do ambiente para Mangaba AI

Este script ajuda a configurar o ambiente de desenvolvimento de forma interativa.
"""

import sys
import subprocess
import shutil
from pathlib import Path


class Colors:
    """Cores para output no terminal"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class EnvironmentSetup:
    """Classe para configuração do ambiente"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.env_template = self.project_root / ".env.template"
        self.requirements_file = self.project_root / "requirements.txt"
        self.test_requirements_file = self.project_root / "requirements-test.txt"

    def print_header(self):
        """Imprime cabeçalho do script"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("=" * 60)
        print("    MANGABA AI - CONFIGURAÇÃO DO AMBIENTE")
        print("=" * 60)
        print(f"{Colors.END}")
        print("Este script irá ajudá-lo a configurar o ambiente de desenvolvimento.")
        print()

    def check_python_version(self) -> bool:
        """Verifica se a versão do Python é compatível"""
        print(f"{Colors.YELLOW}🐍 Verificando versão do Python...{Colors.END}")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(
                f"{Colors.RED}❌ Python 3.8+ é necessário. Versão atual: {version.major}.{version.minor}{Colors.END}"
            )
            return False

        print(
            f"{Colors.GREEN}✅ Python {version.major}.{version.minor}.{version.micro} - OK{Colors.END}"
        )
        return True

    def check_pip(self) -> bool:
        """Verifica se pip está disponível"""
        print(f"{Colors.YELLOW}📦 Verificando pip...{Colors.END}")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
            )
            print(f"{Colors.GREEN}✅ pip disponível{Colors.END}")
            return True
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ pip não encontrado{Colors.END}")
            return False

    def create_virtual_environment(self) -> bool:
        """Cria ambiente virtual se não existir"""
        venv_path = self.project_root / "venv"

        if venv_path.exists():
            print(f"{Colors.GREEN}✅ Ambiente virtual já existe{Colors.END}")
            return True

        print(f"{Colors.YELLOW}🔧 Criando ambiente virtual...{Colors.END}")

        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print(
                f"{Colors.GREEN}✅ Ambiente virtual criado em: {venv_path}{Colors.END}"
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Erro ao criar ambiente virtual: {e}{Colors.END}")
            return False

    def install_dependencies(self, include_test_deps: bool = False) -> bool:
        """Instala dependências do projeto"""
        print(f"{Colors.YELLOW}📚 Instalando dependências...{Colors.END}")

        # Instala dependências principais
        if self.requirements_file.exists():
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(self.requirements_file),
                    ],
                    check=True,
                )
                print(
                    f"{Colors.GREEN}✅ Dependências principais instaladas{Colors.END}"
                )
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}❌ Erro ao instalar dependências: {e}{Colors.END}")
                return False

        # Instala dependências de teste se solicitado
        if include_test_deps and self.test_requirements_file.exists():
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(self.test_requirements_file),
                    ],
                    check=True,
                )
                print(f"{Colors.GREEN}✅ Dependências de teste instaladas{Colors.END}")
            except subprocess.CalledProcessError as e:
                print(
                    f"{Colors.YELLOW}⚠️ Erro ao instalar dependências de teste: {e}{Colors.END}"
                )

        return True

    def setup_environment_file(self) -> bool:
        """Configura arquivo .env"""
        print(f"{Colors.YELLOW}⚙️ Configurando arquivo de ambiente...{Colors.END}")

        # Verifica se .env já existe
        if self.env_file.exists():
            response = input(
                f"{Colors.YELLOW}Arquivo .env já existe. Sobrescrever? (s/N): {Colors.END}"
            )
            if response.lower() not in ["s", "sim", "y", "yes"]:
                print(f"{Colors.GREEN}✅ Mantendo arquivo .env existente{Colors.END}")
                return True

        # Copia template se existir
        if self.env_template.exists():
            shutil.copy2(self.env_template, self.env_file)
            print(
                f"{Colors.GREEN}✅ Arquivo .env criado a partir do template{Colors.END}"
            )
        else:
            # Cria .env básico
            basic_env = """# Configuração básica do Mangaba AI
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-2.5-flash
AGENT_NAME=MangabaAgent
USE_MCP=true
USE_A2A=true
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=true
"""
            with open(self.env_file, "w", encoding="utf-8") as f:
                f.write(basic_env)
            print(f"{Colors.GREEN}✅ Arquivo .env básico criado{Colors.END}")

        return True

    def configure_api_key(self) -> bool:
        """Configura API key interativamente"""
        print(f"{Colors.YELLOW}🔑 Configurando API Key do Google...{Colors.END}")
        print("Para obter sua API key:")
        print("1. Acesse: https://makersuite.google.com/app/apikey")
        print("2. Faça login com sua conta Google")
        print("3. Clique em 'Create API Key'")
        print("4. Copie a chave gerada")
        print()

        api_key = input(
            "Cole sua API key aqui (ou pressione Enter para pular): "
        ).strip()

        if not api_key:
            print(
                f"{Colors.YELLOW}⚠️ API key não configurada. Você precisará editar o arquivo .env manualmente.{Colors.END}"
            )
            return True

        # Atualiza arquivo .env
        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Substitui a linha da API key
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("GOOGLE_API_KEY="):
                    lines[i] = f"GOOGLE_API_KEY={api_key}"
                    break

            with open(self.env_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            print(f"{Colors.GREEN}✅ API key configurada no arquivo .env{Colors.END}")
            return True

        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao configurar API key: {e}{Colors.END}")
            return False

    def test_installation(self) -> bool:
        """Testa a instalação"""
        print(f"{Colors.YELLOW}🧪 Testando instalação...{Colors.END}")

        try:
            # Testa importação básica
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    'from mangaba_agent import MangabaAgent; print("Import OK")',
                ],
                check=True,
                capture_output=True,
            )
            print(f"{Colors.GREEN}✅ Importação básica funcionando{Colors.END}")

            # Testa se pytest está disponível (se dependências de teste foram instaladas)
            try:
                subprocess.run(
                    [sys.executable, "-m", "pytest", "--version"],
                    check=True,
                    capture_output=True,
                )
                print(f"{Colors.GREEN}✅ pytest disponível para testes{Colors.END}")
            except subprocess.CalledProcessError:
                print(
                    f"{Colors.YELLOW}⚠️ pytest não disponível (dependências de teste não instaladas){Colors.END}"
                )

            return True

        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Erro no teste de instalação: {e}{Colors.END}")
            return False

    def print_next_steps(self):
        """Imprime próximos passos"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("=" * 60)
        print("    PRÓXIMOS PASSOS")
        print("=" * 60)
        print(f"{Colors.END}")

        print("1. 📝 Edite o arquivo .env com suas configurações:")
        print(f"   {self.env_file}")
        print()

        print("2. 🧪 Execute os testes (opcional):")
        print("   python -m pytest tests/ -v")
        print()

        print("3. 🚀 Execute um exemplo:")
        print("   python examples/basic_example.py")
        print()

        print("4. 📚 Consulte a documentação:")
        print("   - README.md")
        print("   - SETUP.md")
        print("   - PROTOCOLS.md")
        print()

        print(f"{Colors.GREEN}🎉 Configuração concluída com sucesso!{Colors.END}")

    def run_setup(self):
        """Executa configuração completa"""
        self.print_header()

        # Verificações básicas
        if not self.check_python_version():
            return False

        if not self.check_pip():
            return False

        # Pergunta sobre dependências de teste
        install_test_deps = input(
            f"{Colors.YELLOW}Instalar dependências de teste? (s/N): {Colors.END}"
        )
        include_test_deps = install_test_deps.lower() in ["s", "sim", "y", "yes"]

        # Pergunta sobre ambiente virtual
        create_venv = input(
            f"{Colors.YELLOW}Criar ambiente virtual? (S/n): {Colors.END}"
        )
        if create_venv.lower() not in ["n", "no", "não"]:
            if not self.create_virtual_environment():
                return False

        # Instala dependências
        if not self.install_dependencies(include_test_deps):
            return False

        # Configura arquivo .env
        if not self.setup_environment_file():
            return False

        # Configura API key
        if not self.configure_api_key():
            return False

        # Testa instalação
        if not self.test_installation():
            print(
                f"{Colors.YELLOW}⚠️ Alguns testes falharam, mas a instalação básica está OK{Colors.END}"
            )

        # Próximos passos
        self.print_next_steps()

        return True


def main():
    """Função principal"""
    try:
        setup = EnvironmentSetup()
        success = setup.run_setup()

        if success:
            sys.exit(0)
        else:
            print(
                f"{Colors.RED}❌ Configuração falhou. Consulte as mensagens de erro acima.{Colors.END}"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Configuração cancelada pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
