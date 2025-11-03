"""
NFPA Knowledge Service with RAG (Retrieval Augmented Generation)

This service provides fire safety knowledge from:
1. Free public resources (initial)
2. NFPA 25 standards (when available)
3. Past inspection reports
4. Company procedures
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class NFPAKnowledgeService:
    """Service for querying fire safety knowledge base"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

        # Initialize ChromaDB - use HTTP client if CHROMADB_URL is set, otherwise use local
        chroma_url = os.getenv('CHROMADB_URL', 'http://localhost:8000')

        try:
            # Try to connect to ChromaDB server
            self.client = chromadb.HttpClient(
                host=chroma_url.split('://')[1].split(':')[0],
                port=int(chroma_url.split(':')[-1]),
                settings=Settings(anonymized_telemetry=False)
            )
            # Test connection
            self.client.heartbeat()
            logger.info(f"[NFPA] Connected to ChromaDB server at {chroma_url}")
        except Exception as e:
            # Fallback to local persistent client
            logger.warning(f"[NFPA] Could not connect to ChromaDB server ({e}), using local storage")
            self.chroma_dir = self.data_dir / "chroma_db"
            self.chroma_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(self.chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )

        # Create or get collections
        self.nfpa_collection = self._get_or_create_collection("nfpa_standards")
        self.reports_collection = self._get_or_create_collection("inspection_reports")
        self.procedures_collection = self._get_or_create_collection("company_procedures")
        self.hvac_collection = self._get_or_create_collection("hvac_knowledge")

        # Load initial data if collections are empty
        self._initialize_knowledge_base()

    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )

    def _initialize_knowledge_base(self):
        """Load initial knowledge from data directory"""
        # Check if NFPA collection is empty
        if self.nfpa_collection.count() == 0:
            logger.info("Initializing NFPA knowledge base...")
            self._load_public_resources()
            self._load_nfpa_documents()

        # Check if HVAC collection is empty
        if self.hvac_collection.count() == 0:
            logger.info("Initializing HVAC knowledge base...")
            self._load_hvac_knowledge()

    def _load_public_resources(self):
        """Load free public fire safety resources"""
        public_resources = [
            {
                "id": "pub_001",
                "source": "OSHA Fire Safety Guidelines",
                "section": "General",
                "content": "Fire extinguishers should be inspected monthly and serviced annually. Ensure clear access to all fire protection equipment.",
                "category": "inspection",
                "type": "public_resource"
            },
            {
                "id": "pub_002",
                "source": "ICC Fire Code",
                "section": "Testing",
                "content": "Backflow preventers must be tested annually by a certified tester. Test pressure requirements vary by device type.",
                "category": "testing",
                "equipment": "backflow_preventer",
                "type": "public_resource"
            },
            {
                "id": "pub_003",
                "source": "Fire Safety Best Practices",
                "section": "Sprinkler Systems",
                "content": "Sprinkler systems require quarterly testing. Inspector test connections should be opened to verify water flow and pressure.",
                "category": "testing",
                "equipment": "sprinkler_system",
                "type": "public_resource"
            },
            {
                "id": "pub_004",
                "source": "FM Global Data Sheet",
                "section": "Fire Pumps",
                "content": "Fire pumps should be tested weekly. Run pump for minimum 10 minutes and record suction and discharge pressures.",
                "category": "testing",
                "equipment": "fire_pump",
                "type": "public_resource"
            },
            {
                "id": "pub_005",
                "source": "Fire Protection Equipment Guidelines",
                "section": "Inspection",
                "content": "Visual inspection of sprinkler heads should check for: leaks, corrosion, paint, damage, proper clearance, and correct orientation.",
                "category": "inspection",
                "equipment": "sprinkler_head",
                "type": "public_resource"
            }
        ]

        self._add_documents(self.nfpa_collection, public_resources)
        logger.info(f"Loaded {len(public_resources)} public resources")

    def _load_nfpa_documents(self):
        """Load NFPA documents from data directory (if available)"""
        nfpa_file = self.data_dir / "nfpa" / "nfpa_25.json"

        if nfpa_file.exists():
            try:
                with open(nfpa_file, 'r') as f:
                    nfpa_data = json.load(f)

                # Add type marker for NFPA official content
                for item in nfpa_data:
                    item['type'] = 'nfpa_25_official'
                    item['id'] = f"nfpa_{item.get('section', 'unknown')}"

                self._add_documents(self.nfpa_collection, nfpa_data)
                logger.info(f"Loaded {len(nfpa_data)} NFPA 25 standards")
            except Exception as e:
                logger.error(f"Error loading NFPA documents: {e}")
        else:
            logger.info("No NFPA 25 documents found. Using public resources only.")
            logger.info(f"To add NFPA 25: Place JSON file at {nfpa_file}")

    def _load_hvac_knowledge(self):
        """Load HVAC troubleshooting and technical knowledge"""
        hvac_file = self.data_dir / "hvac" / "hvac_knowledge.json"

        if hvac_file.exists():
            try:
                with open(hvac_file, 'r') as f:
                    hvac_data = json.load(f)

                # Add type marker for HVAC technical content
                for item in hvac_data:
                    item['type'] = 'hvac_technical'
                    if 'id' not in item:
                        item['id'] = f"hvac_{item.get('category', 'unknown')}_{len(hvac_data)}"

                self._add_documents(self.hvac_collection, hvac_data)
                logger.info(f"Loaded {len(hvac_data)} HVAC technical knowledge documents")
            except Exception as e:
                logger.error(f"Error loading HVAC knowledge: {e}")
        else:
            logger.info("No HVAC knowledge file found.")
            logger.info(f"To add HVAC knowledge: Place JSON file at {hvac_file}")

    def _add_documents(self, collection, documents: List[Dict]):
        """Add documents to a collection"""
        if not documents:
            return

        ids = [doc['id'] for doc in documents]
        contents = [doc['content'] for doc in documents]
        metadatas = [
            {k: v for k, v in doc.items() if k not in ['id', 'content']}
            for doc in documents
        ]

        # Generate embeddings
        embeddings = self.embedding_model.encode(contents).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )

    def search_nfpa_standards(self, query: str, n_results: int = 3) -> str:
        """Search NFPA standards and public resources"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Search
            results = self.nfpa_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            if not results['documents'] or not results['documents'][0]:
                return "No relevant information found in knowledge base."

            formatted_results = []
            for i, (doc, metadata) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            )):
                source = metadata.get('source', metadata.get('section', 'Unknown'))
                doc_type = metadata.get('type', 'unknown')

                # Mark if it's official NFPA content
                prefix = "[NFPA 25 Official]" if doc_type == 'nfpa_25_official' else "[Public Resource]"

                formatted_results.append(
                    f"{prefix} {source}:\n{doc}\n"
                )

            return "\n---\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Error searching knowledge base: {str(e)}"

    def search_past_reports(self, query: str, n_results: int = 3) -> str:
        """Search past inspection reports"""
        try:
            if self.reports_collection.count() == 0:
                return "No past inspection reports in database yet."

            query_embedding = self.embedding_model.encode([query])[0].tolist()

            results = self.reports_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            if not results['documents'] or not results['documents'][0]:
                return "No relevant past reports found."

            formatted_results = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                location = metadata.get('location', 'Unknown location')
                date = metadata.get('date', 'Unknown date')
                formatted_results.append(
                    f"[{location} - {date}]:\n{doc}\n"
                )

            return "\n---\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Error searching reports: {e}")
            return f"Error searching reports: {str(e)}"

    def add_inspection_report(self, report: Dict):
        """Add a new inspection report to the knowledge base"""
        try:
            report_data = [{
                'id': report.get('id', f"report_{report['date']}"),
                'content': report.get('summary', ''),
                **{k: v for k, v in report.items() if k != 'summary'}
            }]

            self._add_documents(self.reports_collection, report_data)
            logger.info(f"Added inspection report: {report.get('id')}")

        except Exception as e:
            logger.error(f"Error adding inspection report: {e}")

    def search_hvac_knowledge(self, query: str, n_results: int = 3) -> str:
        """Search HVAC technical knowledge and troubleshooting guides"""
        try:
            if self.hvac_collection.count() == 0:
                return "No HVAC knowledge in database yet."

            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Search
            results = self.hvac_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            if not results['documents'] or not results['documents'][0]:
                return "No relevant HVAC information found."

            formatted_results = []
            for i, (doc, metadata) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            )):
                source = metadata.get('source', 'Unknown')
                section = metadata.get('section', '')
                category = metadata.get('category', '')
                manufacturer = metadata.get('manufacturer', '')

                header_parts = [f"[HVAC Technical]", source]
                if section:
                    header_parts.append(f"- {section}")
                if manufacturer:
                    header_parts.append(f"({manufacturer})")

                formatted_results.append(
                    f"{' '.join(header_parts)}:\n{doc}\n"
                )

            return "\n---\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Error searching HVAC knowledge: {e}")
            return f"Error searching HVAC knowledge: {str(e)}"

    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            "nfpa_standards": self.nfpa_collection.count(),
            "inspection_reports": self.reports_collection.count(),
            "company_procedures": self.procedures_collection.count(),
            "hvac_knowledge": self.hvac_collection.count()
        }


# Singleton instance
_knowledge_service = None

def get_knowledge_service() -> NFPAKnowledgeService:
    """Get or create knowledge service singleton"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = NFPAKnowledgeService()
    return _knowledge_service
