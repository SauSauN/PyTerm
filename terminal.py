import datetime
import random
import socket
import sys
import os
import shutil
import platform
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QInputDialog
import psutil
import gpuinfo

def bytes2human(n):
    """Convertit une taille en octets en format lisible (Ko, Mo, Go)."""
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    i = 0
    while n >= 1024 and i < len(suffixes) - 1:
        n /= 1024.0
        i += 1
    return f"{n:.2f} {suffixes[i]}"

class EmbeddedTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal Étendu - Style PowerShell")
        self.setGeometry(100, 100, 800, 600)

        self.current_dir = os.getcwd()
        self.command_history = []  # Pour stocker l'historique des commandes
        self.history_index = -1  # Index pour naviguer dans l'historique (-1 pour pas de sélection)

        self.terminal_area = QTextEdit(self)
        self.terminal_area.setReadOnly(False)
        self.terminal_area.setStyleSheet("background-color: black; color: green; font-family: Consolas; font-size: 14px;")
        self.terminal_area.installEventFilter(self)

        self.setCentralWidget(self.terminal_area)
        self.write_prompt()
        self.last_protected_position = self.terminal_area.textCursor().position()

        self.game_running = False  # Flag pour savoir si le jeu est en cours


    def write_prompt(self):
        """Affiche l'invite de commande avec un style personnalisé."""
        prompt = f'<span style=" font-weight: bold;">PS {self.current_dir}&gt; </span>'
        self.terminal_area.append(prompt)
        cursor = self.terminal_area.textCursor()
        cursor.movePosition(cursor.End)
        self.terminal_area.setTextCursor(cursor)

    def get_prompt(self):
        """Retourne l'invite de commande dynamique."""
        return f"PS {self.current_dir}> "

    def eventFilter(self, source, event):
        if event.type() == event.KeyPress and source is self.terminal_area:
            cursor = self.terminal_area.textCursor()

            if event.key() == Qt.Key_Return:
                command = self.get_current_command()
                self.execute_command(command)
                self.history_index = -1  # Réinitialiser l'index de l'historique après une commande
                return True
            elif event.key() == Qt.Key_Up:
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.show_history_command()
                return True
            elif event.key() == Qt.Key_Down:
                if self.history_index > -1:
                    self.history_index -= 1
                    self.show_history_command()
                return True
            elif event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
                if not self.can_modify(cursor):
                    return True

        return super().eventFilter(source, event)

    def show_infosyst(self):
        """Affiche des informations détaillées sur l'ordinateur."""
        self.terminal_area.append("Informations détaillées sur l'ordinateur :")
        
        # Informations générales sur le système
        my_system = platform.uname()
        self.terminal_area.append(f"System: {my_system.system}")
        self.terminal_area.append(f"Node Name: {my_system.node}")
        self.terminal_area.append(f"Release: {my_system.release}")
        self.terminal_area.append(f"Version: {my_system.version}")
        self.terminal_area.append(f"Machine: {my_system.machine}")
        self.terminal_area.append(f"Processor: {my_system.processor}")
        
        # Architecture du processeur
        architecture = platform.architecture()[0]
        self.terminal_area.append(f"Architecture: {architecture}")
        
        # Nom de l'utilisateur
        user = os.getlogin()
        self.terminal_area.append(f"Utilisateur courant: {user}")
        
        # Informations Python
        python_version = sys.version
        python_executable = sys.executable
        self.terminal_area.append(f"Python Version: {python_version}")
        self.terminal_area.append(f"Python Executable: {python_executable}")
        
        # Informations sur le réseau (Nom d'hôte et IP)
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        self.terminal_area.append(f"Host Name: {host_name}")
        self.terminal_area.append(f"IP Address: {host_ip}")
        
        # Horloge et heure exacte
        current_time = time.time()
        timestamp = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
        self.terminal_area.append(f"Heure exacte: {timestamp}")
        
        # Utilisation de la mémoire et du processeur (via psutil)
        virtual_memory = psutil.virtual_memory()
        self.terminal_area.append(f"Total RAM: {virtual_memory.total / (1024 ** 3):.2f} GB")
        self.terminal_area.append(f"Available RAM: {virtual_memory.available / (1024 ** 3):.2f} GB")
        self.terminal_area.append(f"Used RAM: {virtual_memory.used / (1024 ** 3):.2f} GB")
        self.terminal_area.append(f"Memory Usage: {virtual_memory.percent}%")
        
        cpu_percent = psutil.cpu_percent(interval=1)
        self.terminal_area.append(f"CPU Usage: {cpu_percent}%")
        
        # Détails sur la batterie (si disponible)
        if psutil.sensors_battery():
            battery = psutil.sensors_battery()
            self.terminal_area.append(f"Battery percent: {battery.percent}%")
            self.terminal_area.append(f"Plugged in: {'Yes' if battery.power_plugged else 'No'}")
            self.terminal_area.append(f"Time left: {battery.secsleft // 60} min" if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Time left: Unlimited")
        
        # Informations sur les partitions de disque
        partitions = psutil.disk_partitions()
        for partition in partitions:
            self.terminal_area.append(f"Partition: {partition.device} (Mount point: {partition.mountpoint})")
            usage = psutil.disk_usage(partition.mountpoint)
            self.terminal_area.append(f"  Total: {bytes2human(usage.total)}")
            self.terminal_area.append(f"  Used: {bytes2human(usage.used)}")
            self.terminal_area.append(f"  Free: {bytes2human(usage.free)}")
            self.terminal_area.append(f"  Usage: {usage.percent}%")
        
        # Informations sur le GPU (si disponible)
        # On peut utiliser une bibliothèque comme `gpuinfo` pour obtenir des informations sur le GPU.
        try:
            gpu = gpuinfo.GPUInfo.get_info()
            self.terminal_area.append(f"GPU Info: {gpu}")
        except ImportError:
            self.terminal_area.append("GPU info non disponible. Installez 'gpuinfo' pour récupérer cette information.")
        
        # Détails sur les processus en cours
        self.terminal_area.append(f"Number of processes: {len(psutil.pids())}")
        
        # Informations réseau (interfaces réseau)
        net_if_addrs = psutil.net_if_addrs()
        for interface, addresses in net_if_addrs.items():
            for address in addresses:
                if address.family == socket.AF_INET:
                    self.terminal_area.append(f"Interface: {interface} - IP Address: {address.address}")
        
        # Détails sur l'espace disque par répertoire
        self.terminal_area.append("Disk usage by directories:")
        self.show_directory_usage("/")

        self.terminal_area.append("")  # Ligne vide pour aérer
    
    def show_directory_usage(self, path):
        """Affiche l'utilisation de l'espace disque par répertoire."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            self.terminal_area.append(f"Total disk usage of {path}: {bytes2human(total_size)}")
        except Exception as e:
            self.terminal_area.append(f"Error: {str(e)}")
        return

    def get_current_command(self):
        cursor = self.terminal_area.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        line_text = cursor.selectedText()
        return line_text.replace(self.get_prompt(), "").strip()

    def can_modify(self, cursor):
        return cursor.position() >= self.last_protected_position

    def execute_command(self, command):
        self.command_history.append(command)  # Enregistrer la commande dans l'historique
        self.terminal_area.append("")

        if not command:
            self.write_prompt()
            return

        cmd_parts = command.split()
        cmd_name = cmd_parts[0]
        args = cmd_parts[1:]

        try:
            if cmd_name == "help":
                self.show_help()
            elif cmd_name == "color":
                self.change_color(args)  
            elif cmd_name == "ls":
                self.list_directory()
            elif cmd_name == "cd":
                self.change_directory(args)
            elif cmd_name == "mkdir":
                self.create_directory(args)
            elif cmd_name == "rm":
                self.remove_item(args)
            elif cmd_name == "exit":
                self.close_terminal()
            elif cmd_name == "cat":
                self.view_file(args)
            elif cmd_name == "touch":
                self.create_file(args)
            elif cmd_name == "clear":
                self.clear_screen()
            elif cmd_name == "rename":
                self.rename_item(args)
            elif cmd_name == "cp":
                self.copy_item(args)
            elif cmd_name == "mv":
                self.move_item(args)
            elif cmd_name == "tree":
                self.show_tree()
            elif cmd_name == "whoami":
                self.show_user()
            elif cmd_name == "pwd":
                self.show_current_directory()
            elif cmd_name == "history":
                self.show_history()
            elif cmd_name == "infosyst":
                self.show_infosyst()
            elif cmd_name == "gamerun":
                self.run_game()  # Lance le jeu de devinette
            else:
                self.show_message(f"Commande inconnue : {cmd_name}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")
        
        self.terminal_area.append("")  # Ajoute une ligne vide après chaque commande exécutée
        self.write_prompt()

    def change_color(self, args):
        """Change la couleur du texte et du fond du terminal."""
        if len(args) != 2:
            self.show_message("Usage : color <text_color> <background_color>")
            return

        text_color = args[0].lower()
        background_color = args[1].lower()

        color_map = {
            "black": "black", "white": "white", "red": "red", "green": "green",
            "blue": "blue", "yellow": "yellow", "cyan": "cyan", "magenta": "magenta",
            "gray": "gray"
        }

        if text_color not in color_map or background_color not in color_map:
            self.show_message("Les couleurs disponibles sont : black, white, red, green, blue, yellow, cyan, magenta, gray.")
            return

        # Appliquer les couleurs
        self.terminal_area.setStyleSheet(f"background-color: {color_map[background_color]}; color: {color_map[text_color]}; font-family: Consolas; font-size: 14px;")
        self.show_message(f"Couleur du texte changée en {text_color} et fond en {background_color}.")

    def run_game(self):
        if self.game_running:
            self.show_message("Un jeu est déjà en cours !")
            return
        
        self.game_running = True
        self.show_message("Bienvenue dans le jeu de devinette de nombre !")
        self.show_message("Je pense à un nombre entre 1 et 100. Essayez de deviner !")

        number_to_guess = random.randint(1, 100)
        attempts = 0

        while True:
            # Demander à l'utilisateur d'entrer sa réponse
            guess, ok = QInputDialog.getInt(self, "Devinez le nombre", 
                                            "Entrez un nombre entre 1 et 100 :", 
                                            50, 1, 100, 1)
            if not ok:
                break  # Si l'utilisateur annule, on arrête le jeu

            attempts += 1

            if guess < number_to_guess:
                self.show_message("C'est plus grand ! Essayez encore.")
            elif guess > number_to_guess:
                self.show_message("C'est plus petit ! Essayez encore.")
            else:
                self.show_message(f"Félicitations ! Vous avez deviné le nombre en {attempts} tentatives.")
                self.show_message("Voulez-vous jouer à nouveau ? (oui/non)")
                play_again, ok = QInputDialog.getText(self, "Jouer à nouveau", "Voulez-vous jouer encore ?")
                if play_again.lower() != 'oui':
                    self.show_message("Merci d'avoir joué !")
                    self.game_running = False
                break

    def show_help(self):
        help_message = """
Commandes disponibles :
    📚 help          - Afficher cette aide
    📂 ls            - Lister les fichiers et répertoires
    🎮 gamerun       - Lancer un jeu de devinette de nombre
    📁 cd <path>     - Changer de répertoire
    🗂️ mkdir <name>  - Créer un nouveau répertoire
    🗑️ rm <name>     - Supprimer un fichier ou répertoire
    📝 cat <file>    - Afficher le contenu d'un fichier
    ✨ touch <file>  - Créer un fichier vide
    🧹 clear         - Effacer l'écran du terminal
    ✏️ rename <old> <new> - Renommer un fichier ou répertoire
    📄 cp <src> <dest> - Copier un fichier ou répertoire
    🚚 mv <src> <dest> - Déplacer un fichier ou répertoire
    🌳 tree          - Afficher la structure des fichiers
    👤 whoami        - Afficher l'utilisateur
    📌 pwd           - Afficher le répertoire courant
    🕒 history       - Afficher l'historique des commandes
    💻 infosyst      - Afficher les informations du système actuel
    🚪 exit          - Quitter le terminal
        """
        self.show_message(help_message)

    def list_directory(self):
        items = os.listdir(self.current_dir)
        self.show_message("\n".join(items))

    def change_directory(self, args):
        if not args:
            self.show_message("Usage : cd <path>")
            return
        try:
            os.chdir(args[0])
            self.current_dir = os.getcwd()
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def create_directory(self, args):
        if not args:
            self.show_message("Usage : mkdir <name>")
            return
        try:
            os.mkdir(os.path.join(self.current_dir, args[0]))
            self.show_message(f"Répertoire créé : {args[0]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def remove_item(self, args):
        if not args:
            self.show_message("Usage : rm <name>")
            return
        try:
            path = os.path.join(self.current_dir, args[0])
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.show_message(f"Supprimé : {args[0]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def view_file(self, args):
        if not args:
            self.show_message("Usage : cat <file>")
            return
        try:
            with open(os.path.join(self.current_dir, args[0]), "r") as f:
                self.show_message(f.read())
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def create_file(self, args):
        if not args:
            self.show_message("Usage : touch <file>")
            return
        try:
            open(os.path.join(self.current_dir, args[0]), "a").close()
            self.show_message(f"Fichier créé : {args[0]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def clear_screen(self):
        self.terminal_area.clear()

    def rename_item(self, args):
        if len(args) < 2:
            self.show_message("Usage : rename <old> <new>")
            return
        try:
            shutil.move(os.path.join(self.current_dir, args[0]), os.path.join(self.current_dir, args[1]))
            self.show_message(f"Renommé : {args[0]} -> {args[1]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def copy_item(self, args):
        if len(args) < 2:
            self.show_message("Usage : cp <src> <dest>")
            return
        try:
            src = os.path.join(self.current_dir, args[0])
            dest = os.path.join(self.current_dir, args[1])
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy(src, dest)
            self.show_message(f"Copié : {args[0]} -> {args[1]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def move_item(self, args):
        if len(args) < 2:
            self.show_message("Usage : mv <src> <dest>")
            return
        try:
            shutil.move(os.path.join(self.current_dir, args[0]), os.path.join(self.current_dir, args[1]))
            self.show_message(f"Déplacé : {args[0]} -> {args[1]}")
        except Exception as e:
            self.show_message(f"Erreur : {e}")

    def show_tree(self):
        def walk_dir(path, indent=0):
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                self.show_message(" " * indent + "|-- " + item)
                if os.path.isdir(full_path):
                    walk_dir(full_path, indent + 4)
        walk_dir(self.current_dir)

    def show_user(self):
        self.show_message(os.getlogin())

    def show_current_directory(self):
        self.show_message(self.current_dir)

    def show_history(self):
        self.show_message("\n".join(self.command_history))

    def close_terminal(self):
        self.show_message("Au revoir !")
        QApplication.instance().quit()

    def show_message(self, message):
        """Affiche un message dans le terminal."""
        self.terminal_area.append(message)

    def show_history_command(self):
        """Affiche la commande de l'historique correspondant à l'index actuel."""
        cursor = self.terminal_area.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)

        # Remplacer la ligne actuelle par la commande historique ou une ligne vide
        if self.history_index == -1:
            cursor.insertText(self.get_prompt())
        else:
            command = self.command_history[-(self.history_index + 1)]
            cursor.insertText(self.get_prompt() + command)

        self.terminal_area.setTextCursor(cursor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = EmbeddedTerminal()
    terminal.show()
    sys.exit(app.exec_())
