#!/usr/bin/env python3
"""
AWS Bedrock Agent Integration with Neo4j Knowledge Graph
Uses AWS Bedrock to create an AI agent that can query the biomedical graph
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import boto3
from typing import Dict, List, Any


class BiomedicalGraphAgent:
    """AI Agent powered by AWS Bedrock that queries Neo4j knowledge graph"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Neo4j connection
        self.neo4j_uri = os.getenv('NEO4J_URI')
        self.neo4j_username = os.getenv('NEO4J_USERNAME')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD')
        self.neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')

        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )

        # AWS Bedrock client
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        print("=" * 80)
        print("AWS BEDROCK AGENT + Neo4j KNOWLEDGE GRAPH")
        print("=" * 80)
        print(f"✓ Connected to Neo4j: {self.neo4j_uri}")
        print(f"✓ AWS Bedrock client initialized")

    def close(self):
        """Close connections"""
        self.driver.close()

    def query_graph(self, cypher_query: str) -> List[Dict]:
        """Execute Cypher query against Neo4j"""
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(cypher_query)
            return [dict(record) for record in result]

    def get_drug_treatments(self, disease_name: str) -> List[Dict]:
        """Find all drugs that treat a specific disease"""
        query = """
        MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
        WHERE dis.name CONTAINS $disease_name
        RETURN d.name as drug, d.mechanism as mechanism,
               r.efficacyRate as efficacy, dis.name as disease
        ORDER BY r.efficacyRate DESC
        """
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query, disease_name=disease_name)
            return [dict(record) for record in result]

    def get_drug_targets(self, drug_name: str) -> List[Dict]:
        """Find protein targets for a specific drug"""
        query = """
        MATCH (d:Drug)-[r:TARGETS]->(p:Protein)
        WHERE d.name CONTAINS $drug_name
        RETURN d.name as drug, p.name as protein, p.proteinClass as proteinClass,
               r.bindingAffinity as affinity, r.mechanismType as mechanismType
        """
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    def get_disease_genes(self, disease_name: str) -> List[Dict]:
        """Find genes associated with a disease"""
        query = """
        MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease)
        WHERE d.name CONTAINS $disease_name
        RETURN g.symbol as gene, g.name as geneName,
               r.associationStrength as strength, r.evidenceLevel as evidence
        ORDER BY r.associationStrength DESC
        """
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query, disease_name=disease_name)
            return [dict(record) for record in result]

    def get_gene_disease_drug_pathway(self, gene_symbol: str) -> List[Dict]:
        """Find complete pathway: Gene → Disease → Drug"""
        query = """
        MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
        WHERE g.symbol = $gene_symbol
        RETURN g.symbol as gene, dis.name as disease, d.name as drug,
               t.efficacyRate as efficacy
        ORDER BY t.efficacyRate DESC
        """
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query, gene_symbol=gene_symbol)
            return [dict(record) for record in result]

    def get_clinical_trials(self, drug_name: str = None, disease_name: str = None) -> List[Dict]:
        """Find clinical trials by drug or disease"""
        if drug_name:
            query = """
            MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
            WHERE d.name CONTAINS $drug_name
            MATCH (t)-[:STUDIES]->(dis:Disease)
            RETURN t.title as trial, t.phase as phase, t.status as status,
                   t.enrollment as enrollment, d.name as drug, dis.name as disease
            ORDER BY t.startDate DESC
            """
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run(query, drug_name=drug_name)
                return [dict(record) for record in result]
        elif disease_name:
            query = """
            MATCH (t:ClinicalTrial)-[:STUDIES]->(dis:Disease)
            WHERE dis.name CONTAINS $disease_name
            MATCH (t)-[:INVESTIGATES]->(d:Drug)
            RETURN t.title as trial, t.phase as phase, t.status as status,
                   t.enrollment as enrollment, d.name as drug, dis.name as disease
            ORDER BY t.startDate DESC
            """
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run(query, disease_name=disease_name)
                return [dict(record) for record in result]
        return []

    def get_adverse_events(self, drug_name: str) -> List[Dict]:
        """Find adverse events reported for a drug"""
        query = """
        MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
        WHERE d.name CONTAINS $drug_name
        RETURN DISTINCT e.name as event, e.severity as severity,
               e.category as category, e.frequency as frequency
        ORDER BY e.severity DESC
        """
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    def get_high_impact_researchers(self, specialization: str = None) -> List[Dict]:
        """Find high-impact researchers"""
        if specialization:
            query = """
            MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
            WHERE r.specialization CONTAINS $specialization AND r.hIndex >= 70
            RETURN r.name as researcher, r.specialization as specialization,
                   r.hIndex as hIndex, r.totalPublications as publications,
                   i.name as institution
            ORDER BY r.hIndex DESC
            """
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run(query, specialization=specialization)
                return [dict(record) for record in result]
        else:
            query = """
            MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
            WHERE r.hIndex >= 70
            RETURN r.name as researcher, r.specialization as specialization,
                   r.hIndex as hIndex, r.totalPublications as publications,
                   i.name as institution
            ORDER BY r.hIndex DESC
            """
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run(query)
                return [dict(record) for record in result]

    def ask_bedrock(self, question: str, context: str) -> str:
        """Query AWS Bedrock with context from Neo4j"""
        prompt = f"""You are a biomedical AI assistant with access to a knowledge graph.

Context from knowledge graph:
{context}

User question: {question}

Provide a detailed, factual answer based on the knowledge graph data above.
Include specific numbers, names, and relationships when available.
If the data doesn't contain enough information, say so clearly.
"""

        try:
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            return f"Error calling Bedrock: {str(e)}"

    def answer_question(self, question: str) -> str:
        """Answer a natural language question by querying the graph and using Bedrock"""

        question_lower = question.lower()

        # Route to appropriate graph query based on question
        if "treat" in question_lower and ("cancer" in question_lower or "diabetes" in question_lower or "alzheimer" in question_lower):
            # Extract disease name
            if "lung cancer" in question_lower or "nsclc" in question_lower:
                results = self.get_drug_treatments("Lung Cancer")
            elif "diabetes" in question_lower:
                results = self.get_drug_treatments("Diabetes")
            elif "alzheimer" in question_lower:
                results = self.get_drug_treatments("Alzheimer")
            else:
                results = []

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        elif "target" in question_lower or "protein" in question_lower:
            # Extract drug name
            if "pembrolizumab" in question_lower:
                results = self.get_drug_targets("Pembrolizumab")
            elif "nivolumab" in question_lower:
                results = self.get_drug_targets("Nivolumab")
            else:
                results = []

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        elif "gene" in question_lower or "brca" in question_lower or "egfr" in question_lower:
            # Gene-disease-drug pathway
            if "brca1" in question_lower:
                results = self.get_gene_disease_drug_pathway("BRCA1")
            elif "egfr" in question_lower:
                results = self.get_gene_disease_drug_pathway("EGFR")
            else:
                results = []

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        elif "trial" in question_lower or "clinical" in question_lower:
            # Clinical trials
            if "pembrolizumab" in question_lower:
                results = self.get_clinical_trials(drug_name="Pembrolizumab")
            elif "lung cancer" in question_lower:
                results = self.get_clinical_trials(disease_name="Lung Cancer")
            else:
                results = []

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        elif "adverse" in question_lower or "side effect" in question_lower:
            # Adverse events
            if "pembrolizumab" in question_lower:
                results = self.get_adverse_events("Pembrolizumab")
            elif "nivolumab" in question_lower:
                results = self.get_adverse_events("Nivolumab")
            else:
                results = []

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        elif "researcher" in question_lower:
            # High-impact researchers
            if "oncology" in question_lower:
                results = self.get_high_impact_researchers("Oncology")
            elif "alzheimer" in question_lower:
                results = self.get_high_impact_researchers("Alzheimer")
            else:
                results = self.get_high_impact_researchers()

            context = json.dumps(results, indent=2)
            return self.ask_bedrock(question, context)

        else:
            return "I couldn't understand your question. Try asking about:\n" + \
                   "- What drugs treat [disease]?\n" + \
                   "- What does [drug] target?\n" + \
                   "- What genes are associated with [disease]?\n" + \
                   "- What clinical trials exist for [drug/disease]?\n" + \
                   "- What are the adverse events of [drug]?\n" + \
                   "- Who are the high-impact researchers in [field]?"


def demo_agent():
    """Demonstration of the agent"""

    agent = BiomedicalGraphAgent()

    print("\n" + "=" * 80)
    print("DEMONSTRATION: AI AGENT QUERYING KNOWLEDGE GRAPH")
    print("=" * 80)

    # Example questions
    questions = [
        "What drugs treat lung cancer?",
        "What protein does Pembrolizumab target?",
        "What genes are associated with breast cancer?",
        "What are the adverse events of Pembrolizumab?",
        "Who are the leading researchers in Alzheimer's disease?",
        "What clinical trials investigated Pembrolizumab for melanoma?"
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 80}")
        print(f"Question {i}: {question}")
        print("=" * 80)

        answer = agent.answer_question(question)
        print(f"\nAnswer:\n{answer}")

        if i < len(questions):
            print("\n" + "-" * 80)

    agent.close()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE!")
    print("=" * 80)


def interactive_mode():
    """Interactive Q&A mode"""

    agent = BiomedicalGraphAgent()

    print("\n" + "=" * 80)
    print("INTERACTIVE MODE - Ask questions about the biomedical knowledge graph")
    print("=" * 80)
    print("\nType 'quit' to exit\n")

    while True:
        try:
            question = input("\nYour question: ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                break

            if not question:
                continue

            print("\nThinking...")
            answer = agent.answer_question(question)
            print(f"\nAnswer:\n{answer}")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

    agent.close()


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        demo_agent()


if __name__ == "__main__":
    main()
