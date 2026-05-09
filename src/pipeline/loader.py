import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document


def load_pdfs(pdf_dir: str = "data/raw") -> List[Document]:
    documents = []
    pdf_path = Path(pdf_dir)

    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"{pdf_dir} 에 PDF 파일이 없습니다.")

    for pdf_file in sorted(pdf_files):
        print(f"  로딩 중: {pdf_file.name}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source_file"] = pdf_file.name
            documents.extend(docs)
            print(f"    → {len(docs)}페이지")
        except Exception as e:
            print(f"    [WARN] 로딩 실패: {e}")

    print(f"\n총 {len(documents)}페이지 로딩 완료")
    return documents
