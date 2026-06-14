#!/usr/bin/env python
"""
Script de configuração automática com suporte a UV.
Funciona tanto com pip quanto com uv.
"""

import sys
import subprocess
import shutil
from pathlib import Path


class SetupManager:
    """Gerencia a configuração automática do projeto."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        self.env_file = self.project_root / ".env"
        self.config_template = self.project_root / "config_template.json"
        self.has_uv = self._check_uv()
        self.has_pip = self._check_pip()

    def _check_uv(self) -> bool:
        """Verifica se UV está instalado."""
        try:
            subprocess.run(["uv", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_pip(self) -> bool:
        """Verifica se pip está disponível."""
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def print_header(self, text: str):
        """Imprime cabeçalho colorido."""
        print(f"\n{'=' * 60}")
        print("  🥭 Mangaba AI - Setup Automático")
        print(f"  {text}")
        print(f"{'=' * 60}\n")

    def print_step(self, number: int, text: str):
        """Imprime passo do setup."""
        print(f"\n  [{number}] {text}")
        print(f"  {'-' * 55}")

    def print_success(self, text: str):
        """Imprime mensagem de sucesso."""
        print(f"  ✅ {text}")

    def print_warning(self, text: str):
        """Imprime aviso."""
        print(f"  ⚠️  {text}")

    def print_error(self, text: str):
        """Imprime erro."""
        print(f"  ❌ {text}")

    def run_command(self, cmd: list, description: str = "") -> bool:
        """Executa comando shell."""
        try:
            if description:
                print(f"    → {description}")
            subprocess.run(cmd, cwd=str(self.project_root), check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Falha ao executar: {' '.join(cmd)}")
            print(f"       Erro: {e}")
            return False
        except FileNotFoundError:
            self.print_error(f"Comando não encontrado: {cmd[0]}")
            return False

    def step_1_check_python(self):
        """Passo 1: Verificar Python."""
        self.print_step(1, "Verificando Python")

        version = sys.version_info
        print(f"    Python {version.major}.{version.minor}.{version.micro}")
        print(f"    Executável: {sys.executable}")

        if version >= (3, 8):
            self.print_success(f"Python {version.major}.{version.minor} compatível!")
            return True
        else:
            self.print_error(
                f"Python {version.major}.{version.minor} não suportado! Requer 3.8+"
            )
            return False

    def step_2_check_installers(self):
        """Passo 2: Verificar gerenciadores disponíveis."""
        self.print_step(2, "Verificando gerenciadores de pacotes")

        if self.has_uv:
            self.print_success("UV está instalado")
            print("    Recomendação: Usando UV (mais rápido!)")
            return True
        elif self.has_pip:
            self.print_warning("UV não encontrado, usando pip")
            print("    Instale UV para melhor performance:")
            if sys.platform == "win32":
                print("      winget install astral-sh.uv")
            else:
                print("      curl -LsSf https://astral.sh/uv/install.sh | sh")
            return True
        else:
            self.print_error("Nenhum gerenciador de pacotes encontrado!")
            return False

    def step_3_create_venv(self):
        """Passo 3: Criar ambiente virtual."""
        self.print_step(3, "Criando ambiente virtual")

        if self.venv_path.exists():
            self.print_warning(f"Ambiente virtual já existe em {self.venv_path}")
            return True

        if self.has_uv:
            if self.run_command(["uv", "venv"], "Criando venv com UV"):
                self.print_success(f"Ambiente virtual criado: {self.venv_path}")
                return True
        else:
            if self.run_command(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                "Criando venv padrão",
            ):
                self.print_success(f"Ambiente virtual criado: {self.venv_path}")
                return True

        return False

    def step_4_install_dependencies(self):
        """Passo 4: Instalar dependências."""
        self.print_step(4, "Instalando dependências")

        if self.has_uv:
            if self.run_command(["uv", "sync"], "Sincronizando com UV"):
                self.print_success("Dependências instaladas com UV")
                return True
        else:
            if self.run_command(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                "Instalando pacote em modo desenvolvimento",
            ):
                self.print_success("Dependências instaladas com pip")
                return True

        return False

    def step_5_setup_env_file(self):
        """Passo 5: Configurar arquivo .env."""
        self.print_step(5, "Configurando arquivo .env")

        if self.env_file.exists():
            self.print_warning(f"Arquivo {self.env_file.name} já existe")
            return True

        if not self.config_template.exists():
            self.print_warning(f"Template {self.config_template.name} não encontrado")
            self.print_warning("Criando .env vazio...")
            self.env_file.touch()
            return True

        try:
            shutil.copy(str(self.config_template), str(self.env_file))
            self.print_success("Arquivo .env criado")
            print(f"    📝 Edite {self.env_file} com suas credenciais:")
            print("       GOOGLE_API_KEY=sua_chave_aqui")
            return True
        except Exception as e:
            self.print_error(f"Falha ao criar .env: {e}")
            return False

    def step_6_validate_setup(self):
        """Passo 6: Validar setup."""
        self.print_step(6, "Validando setup")

        validation_script = self.project_root / "scripts" / "validate_env.py"

        if not validation_script.exists():
            self.print_warning("Script de validação não encontrado")
            return True

        if self.has_uv:
            return self.run_command(
                ["uv", "run", "python", str(validation_script)],
                "Executando validação com UV",
            )
        else:
            return self.run_command(
                [sys.executable, str(validation_script)], "Executando validação"
            )

    def run_setup(self):
        """Executa setup completo."""
        self.print_header("Configuração Automática em Progresso")

        steps = [
            ("Python", self.step_1_check_python),
            ("Gerenciadores", self.step_2_check_installers),
            ("Ambiente Virtual", self.step_3_create_venv),
            ("Dependências", self.step_4_install_dependencies),
            ("Arquivo .env", self.step_5_setup_env_file),
            ("Validação", self.step_6_validate_setup),
        ]

        failed_steps = []

        for step_name, step_func in steps:
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                self.print_error(f"Erro inesperado: {e}")
                failed_steps.append(step_name)

        # Resumo final
        self.print_header("Setup Concluído")

        if not failed_steps:
            self.print_success("✨ Setup completado com sucesso!")
            print("\n  Próximos passos:")
            print("  ─────────────────────────────────────────────")

            if self.has_uv:
                print("  1. Execute: uv run python examples/basic_example.py")
                print("  2. Ou use: uv run pytest (para rodar testes)")
            else:
                activate_cmd = (
                    ".venv\\Scripts\\Activate.ps1"
                    if sys.platform == "win32"
                    else "source .venv/bin/activate"
                )
                print(f"  1. Ative o venv: {activate_cmd}")
                print("  2. Execute: python examples/basic_example.py")
                print("  3. Ou use: pytest (para rodar testes)")

            print("\n  📚 Documentação: docs/UV_SETUP.md")
            print("  💡 Agente exemplo: examples/basic_example.py")
            print()
        else:
            self.print_error(f"Setup falhou em {len(failed_steps)} etapa(s):")
            for step in failed_steps:
                print(f"    • {step}")
            print("\n  Tente novamente ou consulte a documentação.")
            print()
            return False

        return True


def main():
    """Função principal."""
    try:
        manager = SetupManager()
        success = manager.run_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Setup cancelado pelo usuário.")
        return 1
    except Exception as e:
        print(f"\n  ❌ Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
