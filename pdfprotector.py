# from pypdf import PdfReader, PdfWriter
# from getpass import getpass
# import os

# def list_pdfs():
#     pdfs = [f for f in os.listdir() if f.endswith(".pdf")]

#     if not pdfs:
#         print("No PDF files found in current directory.")
#         return []

#     print("\nAvailable PDF files:\n")

#     for i, pdf in enumerate(pdfs, start=1):
#         print(f"{i}. {pdf}")

#     return pdfs


# def encrypt_pdf(input_pdf, password):
#     reader = PdfReader(input_pdf)
#     writer = PdfWriter()

#     for page in reader.pages:
#         writer.add_page(page)

#     writer.encrypt(password)

#     output_pdf = f"encrypted_{input_pdf}"

#     with open(output_pdf, "wb") as f:
#         writer.write(f)

#     print(f"\nPDF encrypted successfully!")
#     print(f"Saved as: {output_pdf}")


# def main():
#     pdfs = list_pdfs()

#     if not pdfs:
#         return

#     try:
#         choice = int(input("\nEnter PDF number: "))

#         if choice < 1 or choice > len(pdfs):
#             print("Invalid choice.")
#             return

#         selected_pdf = pdfs[choice - 1]

#         password = getpass("Enter password for PDF: ")

#         if not password.strip():
#             print("Password cannot be empty.")
#             return

#         encrypt_pdf(selected_pdf, password)

#     except ValueError:
#         print("Please enter a valid number.")

#     except Exception as e:
#         print(f"Error: {e}")


# if __name__ == "__main__":
#     main()



# --------------------------------NEW ONE-----------------------------------
import os
from pathlib import Path
from getpass import getpass

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from pypdf import PdfReader, PdfWriter

import win32com.client as win32


console = Console()


# ==========================================
# PDF ENCRYPTION
# ==========================================
def encrypt_pdf(file_path, password):
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        path = Path(file_path)

        output_file = path.with_name(
            f"{path.stem}_encrypted{path.suffix}"
        )

        with open(output_file, "wb") as f:
            writer.write(f)

        console.print(f"[green]✔ PDF encrypted:[/green] {output_file}")

    except Exception as e:
        console.print(f"[red]PDF Error:[/red] {e}")


# ==========================================
# EXCEL / WORD ENCRYPTION
# ==========================================
def encrypt_office_file(file_path, password):
    try:
        path = Path(file_path)

        ext = path.suffix.lower()

        if ext == ".xlsx":
            app = win32.gencache.EnsureDispatch("Excel.Application")
            app.Visible = False

            wb = app.Workbooks.Open(str(path.resolve()))

            output_file = path.with_name(
                f"{path.stem}_encrypted{path.suffix}"
            )

            wb.SaveAs(
                str(output_file.resolve()),
                Password=password
            )

            wb.Close(False)
            app.Quit()

            console.print(f"[green]✔ Excel encrypted:[/green] {output_file}")

        elif ext == ".docx":
            app = win32.gencache.EnsureDispatch("Word.Application")
            app.Visible = False

            doc = app.Documents.Open(str(path.resolve()))

            output_file = path.with_name(
                f"{path.stem}_encrypted{path.suffix}"
            )

            doc.SaveAs(
                str(output_file.resolve()),
                Password=password
            )

            doc.Close(False)
            app.Quit()

            console.print(f"[green]✔ Word encrypted:[/green] {output_file}")

    except Exception as e:
        console.print(f"[red]Office Error:[/red] {e}")


# ==========================================
# SCAN FILES
# ==========================================
def scan_files():
    supported = [".pdf", ".xlsx", ".docx"]

    files = []

    for file in os.listdir():
        if Path(file).suffix.lower() in supported:
            files.append(file)

    return files


# ==========================================
# SHOW TABLE
# ==========================================
def show_files(files):
    table = Table(title="Detected Files")

    table.add_column("No", style="cyan")
    table.add_column("Filename", style="green")
    table.add_column("Type", style="yellow")

    for i, file in enumerate(files, start=1):
        table.add_row(str(i), file, Path(file).suffix)

    console.print(table)


# ==========================================
# MAIN
# ==========================================
def main():
    console.print(
        Panel.fit(
            "[bold cyan]SECURE FILE ENCRYPTOR[/bold cyan]\n"
            "PDF | Excel | Word Password Protection",
            border_style="blue",
        )
    )

    files = scan_files()

    if files:
        show_files(files)
    else:
        console.print("[yellow]No supported files found.[/yellow]")

    console.print("\n1. Encrypt from current directory")
    console.print("2. Enter custom file path")
    console.print("3. Exit")

    choice = Prompt.ask(
        "\nEnter choice",
        choices=["1", "2", "3"]
    )

    selected_file = None

    if choice == "1":
        if not files:
            return

        try:
            file_choice = int(
                Prompt.ask("Enter file number")
            )

            if file_choice < 1 or file_choice > len(files):
                console.print("[red]Invalid file number.[/red]")
                return

            selected_file = files[file_choice - 1]

        except ValueError:
            console.print("[red]Invalid input.[/red]")
            return

    elif choice == "2":
        custom_path = Prompt.ask("Enter full file path")

        if not os.path.exists(custom_path):
            console.print("[red]File not found.[/red]")
            return

        selected_file = custom_path

    elif choice == "3":
        return

    password = getpass("Enter password: ")

    if not password.strip():
        console.print("[red]Password cannot be empty.[/red]")
        return

    ext = Path(selected_file).suffix.lower()

    if ext == ".pdf":
        encrypt_pdf(selected_file, password)

    elif ext in [".xlsx", ".docx"]:
        encrypt_office_file(selected_file, password)

    else:
        console.print("[red]Unsupported file type.[/red]")


if __name__ == "__main__":
    main()
