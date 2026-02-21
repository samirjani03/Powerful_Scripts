import pypdf
import getpass
import sys

def encrypt_pdf(input_pdf, output_pdf, password):
    pdf_writer = pypdf.PdfWriter()
    pdf_reader = pypdf.PdfReader(input_pdf)

    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])

    pdf_writer.encrypt(user_password=password)

    with open(output_pdf, 'wb') as output_file:
        pdf_writer.write(output_file)



if __name__ == "__main__":
    if len(sys.argv) == 4:
        input_pdf = sys.argv[1]
        output_pdf = sys.argv[2]
        password = sys.argv[3]
    else:
        input_pdf = input("Enter the path to the PDF file to encrypt: ")
        output_pdf = input("Enter the path for the encrypted PDF file: ")
        password = getpass.getpass("Enter the encryption password: ")

    encrypt_pdf(input_pdf, output_pdf, password)
    print(f"Encrypted PDF saved as {output_pdf}")
