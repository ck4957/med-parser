"""
Advanced MLX Pipeline with Self-Correction and Vector Search Fallback

This demonstrates production-grade error handling:
1. Model generates structured output
2. Validator catches hallucinated codes
3. System retries with more specific prompts
4. Falls back to vector DB for code lookup
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

from mlx_medgemma_pipeline import MedGemmaPipeline

# Vector DB for code lookup (using FAISS for simplicity)
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not installed. Run: pip install faiss-cpu")

logger = logging.getLogger(__name__)


class MedicalCodeVectorDB:
    """
    Lightweight vector database for medical codes.
    In production, this would be a full Pinecone/Weaviate instance.
    """
    
    def __init__(self, code_db_path: Optional[str] = None):
        """
        Initialize with medical code database.
        
        Args:
            code_db_path: Path to JSON file with ICD-10 and RxNorm codes
        """
        self.icd10_codes = self._load_icd10_codes()
        self.rxnorm_codes = self._load_rxnorm_codes()
        
        if FAISS_AVAILABLE:
            self.index = self._build_vector_index()
        else:
            self.index = None
            logger.warning("FAISS not available, using fuzzy string matching")
    
    def _load_icd10_codes(self) -> Dict[str, str]:
        """
        Load ICD-10 codes. In production, load from UMLS or CMS dataset.
        Here we use a small sample for demonstration.
        """
        return {
            "I10": "Essential (primary) hypertension",
            "I11.0": "Hypertensive heart disease with heart failure",
            "E11.9": "Type 2 diabetes mellitus without complications",
            "E11.65": "Type 2 diabetes mellitus with hyperglycemia",
            "I25.10": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
            "I25.119": "Atherosclerotic heart disease of native coronary artery with unspecified angina pectoris",
            "E78.5": "Hyperlipidemia, unspecified",
            "E78.0": "Pure hypercholesterolemia",
            "I63.9": "Cerebral infarction, unspecified",
            "N18.3": "Chronic kidney disease, stage 3",
            "J44.1": "Chronic obstructive pulmonary disease with acute exacerbation",
            "J44.0": "Chronic obstructive pulmonary disease with acute lower respiratory infection",
        }
    
    def _load_rxnorm_codes(self) -> Dict[str, str]:
        """
        Load RxNorm codes. In production, load from NLM RxNorm API.
        """
        return {
            "314076": "Lisinopril 10 MG Oral Tablet",
            "314077": "Lisinopril 20 MG Oral Tablet",
            "861007": "Metformin hydrochloride 1000 MG Oral Tablet",
            "860975": "Metformin hydrochloride 500 MG Oral Tablet",
            "617310": "Atorvastatin 40 MG Oral Tablet",
            "617311": "Atorvastatin 80 MG Oral Tablet",
            "308136": "Amlodipine 5 MG Oral Tablet",
            "197361": "Aspirin 81 MG Oral Tablet",
            "855332": "Metoprolol succinate 50 MG Extended Release Oral Tablet",
            "351761": "Warfarin Sodium 5 MG Oral Tablet",
        }
    
    def _build_vector_index(self):
        """
        Build FAISS index for semantic search.
        In production, use proper embeddings (BERT, etc.)
        """
        # Placeholder - in production use sentence-transformers
        logger.info("Building vector index (placeholder)")
        return None
    
    def search_icd10(self, term: str, threshold: float = 0.7) -> Optional[str]:
        """
        Fuzzy search for ICD-10 code by condition name.
        
        Args:
            term: Condition name (e.g., "diabetes")
            threshold: Similarity threshold (0-1)
            
        Returns:
            Best matching ICD-10 code or None
        """
        term_lower = term.lower()
        
        best_match = None
        best_score = 0.0
        
        for code, description in self.icd10_codes.items():
            desc_lower = description.lower()
            
            # Simple word overlap scoring (in production, use embeddings)
            term_words = set(term_lower.split())
            desc_words = set(desc_lower.split())
            
            if not term_words:
                continue
            
            overlap = len(term_words & desc_words)
            score = overlap / len(term_words)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = code
        
        if best_match:
            logger.info(f"   📍 Vector DB match: '{term}' → {best_match} ({best_score:.2f})")
        
        return best_match
    
    def search_rxnorm(self, term: str, threshold: float = 0.7) -> Optional[str]:
        """
        Fuzzy search for RxNorm code by medication name.
        """
        term_lower = term.lower()
        
        best_match = None
        best_score = 0.0
        
        for code, description in self.rxnorm_codes.items():
            desc_lower = description.lower()
            
            # Check if medication name appears in description
            if term_lower in desc_lower:
                score = 1.0
            else:
                # Word overlap
                term_words = set(term_lower.split())
                desc_words = set(desc_lower.split())
                
                if not term_words:
                    continue
                
                overlap = len(term_words & desc_words)
                score = overlap / len(term_words)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = code
        
        if best_match:
            logger.info(f"   📍 Vector DB match: '{term}' → {best_match} ({best_score:.2f})")
        
        return best_match


class AdvancedMedGemmaPipeline(MedGemmaPipeline):
    """
    Extended pipeline with self-correction and fallback mechanisms.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector_db = MedicalCodeVectorDB()
        self.max_retries = 2
    
    def self_correct_with_retry(
        self,
        transcript: str,
        initial_result: Dict,
        validation_results: Dict
    ) -> Dict:
        """
        If validation fails, retry with more specific prompts.
        
        Args:
            transcript: Original input
            initial_result: First extraction attempt
            validation_results: Validation errors
            
        Returns:
            Corrected result
        """
        logger.info("🔄 Self-correction: Re-prompting model with specific guidance...")
        
        # Identify what failed
        failed_medications = [
            m for m in validation_results.get("medications", [])
            if not m["valid"]
        ]
        failed_conditions = [
            c for c in validation_results.get("conditions", [])
            if not c["valid"]
        ]
        
        if not failed_medications and not failed_conditions:
            return initial_result
        
        # Build correction prompt
        correction_guidance = []
        
        if failed_medications:
            med_names = [m["name"] for m in failed_medications]
            correction_guidance.append(
                f"Please provide valid RxNorm codes for: {', '.join(med_names)}"
            )
        
        if failed_conditions:
            cond_names = [c["name"] for c in failed_conditions]
            correction_guidance.append(
                f"Please provide valid ICD-10 codes for: {', '.join(cond_names)}"
            )
        
        # Create retry prompt
        retry_prompt = f"""<start_of_turn>user
The previous response had invalid medical codes. Please correct:

{chr(10).join(correction_guidance)}

IMPORTANT: Output ONLY valid ICD-10 codes (format: A00-Z99) and RxNorm codes (6-8 digits).

Original transcript:
{transcript}

<end_of_turn>
<start_of_turn>model
"""
        
        # Generate corrected response
        try:
            retry_response = self.generate_response(retry_prompt)
            retry_data = self.extract_json_from_response(retry_response)
            
            if retry_data:
                logger.info("✅ Self-correction successful")
                return retry_data
        
        except Exception as e:
            logger.error(f"❌ Retry failed: {e}")
        
        return initial_result
    
    def fallback_to_vector_db(
        self,
        extracted_data: Dict,
        validation_results: Dict
    ) -> Dict:
        """
        For invalid codes, use vector DB to find correct ones.
        
        Args:
            extracted_data: Model's extraction
            validation_results: Validation status
            
        Returns:
            Corrected data with vector DB lookups
        """
        logger.info("🔍 Vector DB Fallback: Looking up correct codes...")
        
        corrected_data = extracted_data.copy()
        
        # Fix medications
        for i, med in enumerate(corrected_data.get("medications", [])):
            validation = validation_results["medications"][i]
            
            if not validation["valid"]:
                logger.info(f"   ⚠️  Invalid RxNorm code for '{med['name']}'")
                
                # Search vector DB
                correct_code = self.vector_db.search_rxnorm(med["name"])
                
                if correct_code:
                    med["rxnorm_code"] = correct_code
                    med["source"] = "vector_db_fallback"
                    logger.info(f"   ✅ Corrected to: {correct_code}")
                else:
                    logger.warning(f"   ❌ No match found in vector DB")
        
        # Fix conditions
        for i, cond in enumerate(corrected_data.get("conditions", [])):
            validation = validation_results["conditions"][i]
            
            if not validation["valid"]:
                logger.info(f"   ⚠️  Invalid ICD-10 code for '{cond['name']}'")
                
                # Search vector DB
                correct_code = self.vector_db.search_icd10(cond["name"])
                
                if correct_code:
                    cond["icd10_code"] = correct_code
                    cond["source"] = "vector_db_fallback"
                    logger.info(f"   ✅ Corrected to: {correct_code}")
                else:
                    logger.warning(f"   ❌ No match found in vector DB")
        
        return corrected_data
    
    def process_transcript_with_fallback(
        self,
        transcript: str,
        validate: bool = True
    ) -> Dict:
        """
        Enhanced pipeline with retry and fallback logic.
        
        Pipeline:
        1. Initial extraction
        2. FHIR validation
        3. If invalid → Self-correct with retry prompt
        4. If still invalid → Fallback to vector DB
        5. Final validation
        """
        logger.info("=" * 70)
        logger.info("🏥 ADVANCED PIPELINE WITH SELF-CORRECTION")
        logger.info("=" * 70)
        
        # Step 1: Initial extraction
        result = self.process_transcript(transcript, validate=validate)
        
        if not result["success"] or not validate:
            return result
        
        # Step 2: Check if any codes are invalid
        invalid_meds = sum(
            1 for m in result["validation_results"]["medications"]
            if not m["valid"]
        )
        invalid_conds = sum(
            1 for c in result["validation_results"]["conditions"]
            if not c["valid"]
        )
        
        total_invalid = invalid_meds + invalid_conds
        
        if total_invalid == 0:
            logger.info("✅ All codes valid on first attempt")
            return result
        
        logger.warning(f"⚠️  {total_invalid} invalid codes detected")
        
        # Step 3: Self-correction attempt
        corrected_data = self.self_correct_with_retry(
            transcript,
            result["extracted_data"],
            result["validation_results"]
        )
        
        # Re-validate
        logger.info("🔍 Re-validating after self-correction...")
        revalidation_results = {
            "medications": [],
            "conditions": []
        }
        
        for med in corrected_data.get("medications", []):
            is_valid, error = self.validate_fhir_medication(med)
            revalidation_results["medications"].append({
                "name": med.get("name"),
                "valid": is_valid,
                "error": error
            })
        
        for cond in corrected_data.get("conditions", []):
            is_valid, error = self.validate_fhir_condition(cond)
            revalidation_results["conditions"].append({
                "name": cond.get("name"),
                "valid": is_valid,
                "error": error
            })
        
        # Check if still invalid
        still_invalid_meds = sum(1 for m in revalidation_results["medications"] if not m["valid"])
        still_invalid_conds = sum(1 for c in revalidation_results["conditions"] if not c["valid"])
        
        if still_invalid_meds + still_invalid_conds > 0:
            logger.warning(f"⚠️  {still_invalid_meds + still_invalid_conds} codes still invalid")
            
            # Step 4: Vector DB fallback
            final_data = self.fallback_to_vector_db(corrected_data, revalidation_results)
            
            # Final validation
            logger.info("🔍 Final validation after vector DB fallback...")
            final_validation = {
                "medications": [],
                "conditions": []
            }
            
            for med in final_data.get("medications", []):
                is_valid, error = self.validate_fhir_medication(med)
                final_validation["medications"].append({
                    "name": med.get("name"),
                    "valid": is_valid,
                    "error": error,
                    "source": med.get("source", "model")
                })
            
            for cond in final_data.get("conditions", []):
                is_valid, error = self.validate_fhir_condition(cond)
                final_validation["conditions"].append({
                    "name": cond.get("name"),
                    "valid": is_valid,
                    "error": error,
                    "source": cond.get("source", "model")
                })
            
            result["extracted_data"] = final_data
            result["validation_results"] = final_validation
            result["correction_stages"] = ["initial", "self_correct", "vector_db"]
        else:
            logger.info("✅ Self-correction fixed all issues")
            result["extracted_data"] = corrected_data
            result["validation_results"] = revalidation_results
            result["correction_stages"] = ["initial", "self_correct"]
        
        # Summary
        final_invalid = sum(
            1 for m in result["validation_results"]["medications"] if not m["valid"]
        ) + sum(
            1 for c in result["validation_results"]["conditions"] if not c["valid"]
        )
        
        logger.info("=" * 70)
        logger.info(f"📊 FINAL RESULT: {total_invalid - final_invalid}/{total_invalid} codes corrected")
        logger.info("=" * 70)
        
        return result


def main():
    """
    Demo: Show self-correction and fallback mechanisms.
    """
    
    # Transcript with potentially tricky extractions
    sample_transcript = """
    Patient presenting with essential HTN and T2DM.
    Current meds: Lisinopril twenty milligrams daily, Metformin 1 gram BID.
    Starting statin therapy - Atorvastatin 40 at bedtime.
    Patient has history of CAD, needs regular monitoring.
    """
    
    print("\n" + "=" * 70)
    print("🏥 ADVANCED PIPELINE DEMO")
    print("   Self-Correction + Vector DB Fallback")
    print("=" * 70 + "\n")
    
    # Initialize advanced pipeline
    pipeline = AdvancedMedGemmaPipeline(
        model_name="google/gemma-2-27b-it",
        quantization_bits=4,
        temperature=0.1
    )
    
    # Load model
    if not pipeline.load_model():
        print("\n❌ Failed to load model")
        return
    
    print("\n📝 INPUT:")
    print(sample_transcript)
    print("\n" + "-" * 70 + "\n")
    
    # Process with fallback
    result = pipeline.process_transcript_with_fallback(
        transcript=sample_transcript,
        validate=True
    )
    
    # Display
    print("\n📊 FINAL OUTPUT:")
    print(json.dumps(result["extracted_data"], indent=2))
    
    if "correction_stages" in result:
        print(f"\n🔄 Correction stages used: {' → '.join(result['correction_stages'])}")


if __name__ == "__main__":
    main()
