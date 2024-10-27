import pathlib
from pypdf import PdfReader
from extrator.extrator_factory import instanciar

def process_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        text += page.extract_text()

    extrator = instanciar(text)
    if not extrator:
        raise ValueError(f"Arquivo não reconhecido: {file_path}")

    transacoes = extrator.extrair()
    return transacoes
    

def process_directory(directory):
    path = pathlib.Path(directory)
    pdf_files = path.glob("*.pdf")

    transacoes = []
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        try:
            transacoes += process_pdf(pdf_file)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    transacoes = sorted(transacoes, key=lambda t: t["data"])
    for transacao in transacoes:
        print(str(transacao) + "\n")

if __name__ == "__main__":
    process_directory("data/pdf")