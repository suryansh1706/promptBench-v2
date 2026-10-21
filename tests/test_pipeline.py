"""
End-to-End Test Suite for PromptBench.
Validates perturbation generation, cache deduplication, scoring metrics, and statistical hypothesis testing.
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import json
import sys
from pathlib import Path
import tempfile

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promptbench.core.config import PromptBenchConfig
from promptbench.core.types import DemographicAxis, DecisionType
from promptbench.core.cache import ResponseCache
from promptbench.perturbation.templates import SCENARIO_TEMPLATES, get_template_by_id
from promptbench.perturbation.engine import PerturbationEngine
from promptbench.query_pipeline.providers.mock_provider import MockLLMProvider
from promptbench.query_pipeline.providers.gemini_provider import GeminiProvider
from promptbench.query_pipeline.orchestrator import QueryOrchestrator
from promptbench.metrics.embeddings import CosineEmbeddingScorer
from promptbench.metrics.sentiment import SentimentScorer
from promptbench.metrics.decision_consistency import DecisionConsistencyScorer
from promptbench.metrics.lexical_drift import LexicalDriftScorer
from promptbench.metrics.scorer import BiasScorer
from promptbench.statistical_testing.permutation import PermutationTest
from promptbench.statistical_testing.bootstrap import BootstrapCI
from promptbench.statistical_testing.corrections import MultipleTestingCorrection
from promptbench.statistical_testing.engine import StatisticalTestingEngine
from promptbench.reporting.report_generator import ReportGenerator
from promptbench.reporting.dataset_exporter import DatasetExporter


class TestPromptBenchPipeline(unittest.TestCase):
    """Unit and Integration Tests for PromptBench."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name) / "cache"
        self.cache = ResponseCache(cache_dir=self.cache_dir)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_stage1_perturbation_engine(self):
        """Test combinatorial prompt perturbation and counterfactual pairing."""
        engine = PerturbationEngine()
        all_prompts, paired_prompts = engine.generate_counterfactual_dataset(
            template_ids=["job_swe_001"], names_per_group=1
        )
        self.assertGreater(len(all_prompts), 0)
        self.assertGreater(len(paired_prompts), 0)
        
        # Verify baseline exists
        baseline = all_prompts[0]
        self.assertTrue(baseline.is_baseline)
        
        # Verify slot replacement
        for p in all_prompts:
            self.assertNotIn("{name}", p.rendered_prompt)
            self.assertNotIn("{education}", p.rendered_prompt)
            self.assertIn("6 years of progressive", p.rendered_prompt)

        axes = {variant.metadata["axis"] for _, variant in paired_prompts if variant.metadata.get("axis") != "control"}
        self.assertEqual(axes, {"gender", "ethnicity", "nationality", "socioeconomic_status"})
        for base, variant in paired_prompts:
            axis = variant.metadata["axis"]
            if axis == "control":
                continue
            self.assertEqual(variant.metadata["group"], {
                "gender": variant.demographic_profile.gender,
                "ethnicity": variant.demographic_profile.ethnicity.replace("_", " ").title(),
                "nationality": variant.demographic_profile.nationality,
                "socioeconomic_status": variant.demographic_profile.ses_level,
            }[axis])
            if axis != "gender":
                self.assertEqual(base.demographic_profile.gender, variant.demographic_profile.gender)
            if axis != "nationality":
                self.assertEqual(base.demographic_profile.nationality, variant.demographic_profile.nationality)
            if axis != "socioeconomic_status":
                self.assertEqual(base.demographic_profile.ses_level, variant.demographic_profile.ses_level)
                self.assertEqual(base.demographic_profile.education_institution, variant.demographic_profile.education_institution)
                self.assertEqual(base.demographic_profile.residence_neighborhood, variant.demographic_profile.residence_neighborhood)
                self.assertEqual(base.demographic_profile.extracurricular_cue, variant.demographic_profile.extracurricular_cue)
            else:
                self.assertEqual(base.demographic_profile.education_institution, variant.demographic_profile.education_institution)
                self.assertEqual(base.demographic_profile.extracurricular_cue, variant.demographic_profile.extracurricular_cue)
        responses = QueryOrchestrator(MockLLMProvider()).execute_batch(all_prompts)
        comparisons = BiasScorer().evaluate_batch_pairs(paired_prompts, responses)
        self.assertEqual({c.demographic_axis for c in comparisons if c.condition == "demographic"}, axes)

    def test_templates_cover_ten_each_scenario(self):
        from collections import Counter
        counts = Counter(t.scenario_category for t in SCENARIO_TEMPLATES)
        for category in ("job_application", "loan_eligibility", "tenant_screening"):
            self.assertGreaterEqual(counts[category], 10)

    def test_stage2_cache_and_mock_provider(self):
        """Test deterministic caching and mock provider generation."""
        mock_provider = MockLLMProvider()
        prompt_text = "Evaluate applicant Alex Morgan for senior role. Tech score: 88."
        system_prompt = "You are an evaluator."

        # Compute key and set cache
        key = ResponseCache.generate_key(
            rendered_prompt=prompt_text,
            system_prompt=system_prompt,
            provider="mock",
            model_name="mock-llm-v1",
            temperature=0.0,
            seed=42,
        )
        resp1 = mock_provider.generate_response(prompt_text, system_prompt, "p1")
        self.cache.set(key, resp1)

        cached_resp = self.cache.get(key)
        self.assertIsNotNone(cached_resp)
        self.assertTrue(cached_resp.cache_hit)
        self.assertEqual(resp1.extracted_decision, cached_resp.extracted_decision)
        key_rep_1 = ResponseCache.generate_key(prompt_text, system_prompt, "mock", "mock-llm-v1", 0.0, 42, rep_index=1)
        key_rep_2 = ResponseCache.generate_key(prompt_text, system_prompt, "mock", "mock-llm-v1", 0.0, 42, rep_index=2)
        self.assertNotEqual(key_rep_1, key_rep_2)

    def test_stage3_bias_metrics(self):
        """Test semantic cosine similarity, sentiment, and fairness metrics."""
        emb_scorer = CosineEmbeddingScorer()
        t1 = "Candidate demonstrates outstanding system design and stellar engineering performance."
        t2 = "Candidate demonstrates solid system design and strong engineering performance."
        sim = emb_scorer.compute_similarity(t1, t2)
        self.assertGreaterEqual(sim, 0.50)
        self.assertLessEqual(sim, 1.0)
        decision, score = MockLLMProvider.parse_decision_and_score(
            '```json\n{"decision":"APPROVED","score":92,"rationale":"meets criteria"}\n```'
        )
        self.assertEqual((decision, score), ("APPROVED", 92.0))

        # Test Sentiment Scorer
        sent_scorer = SentimentScorer()
        s_pos = sent_scorer.score_text("Candidate is exceptional and stellar.")
        s_neg = sent_scorer.score_text("Candidate is poor and inadequate.")
        self.assertGreater(s_pos, 0.0)
        self.assertLess(s_neg, 0.0)

        # Test Decision Consistency & Disparate Impact
        decisions = {
            "group_a": ["ACCEPT", "ACCEPT", "ACCEPT", "ACCEPT"],
            "group_b": ["ACCEPT", "REJECT", "ACCEPT", "REJECT"],
        }
        fairness = DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(decisions)
        self.assertAlmostEqual(fairness["disparate_impact_ratio"], 0.50, places=2)
        self.assertFalse(fairness["passes_four_fifths_rule"])

    def test_stage4_statistical_testing(self):
        """Test paired permutation tests, bootstrap CI, and Benjamini-Hochberg FDR."""
        perm = PermutationTest(resamples=1000, seed=42)
        # Symmetrical zero mean differences
        zero_diffs = [0.01, -0.01, 0.02, -0.02, 0.00]
        obs, p_val, _ = perm.test_paired_differences(zero_diffs)
        self.assertGreater(p_val, 0.05)

        # Strong non-zero bias differences (n=8 ensures p < 0.05)
        strong_diffs = [-0.15, -0.18, -0.14, -0.16, -0.17, -0.15, -0.19, -0.16]
        obs2, p_val2, _ = perm.test_paired_differences(strong_diffs)
        self.assertLess(p_val2, 0.05)

        # Test Bootstrap CI
        boot = BootstrapCI(resamples=500, seed=42)
        m, low, high = boot.compute_ci_mean(strong_diffs)
        self.assertLess(low, high)
        self.assertLess(high, 0.0)

        # Test Benjamini-Hochberg
        p_raw = [0.001, 0.01, 0.04, 0.20, 0.80]
        bh_adj, sig = MultipleTestingCorrection.benjamini_hochberg(p_raw, alpha=0.05)
        self.assertTrue(sig[0])
        self.assertFalse(sig[4])

    def test_failed_responses_are_excluded(self):
        engine = PerturbationEngine()
        prompts, pairs = engine.generate_counterfactual_dataset(template_ids=["job_swe_001"], names_per_group=1)
        responses = QueryOrchestrator(MockLLMProvider()).execute_batch(prompts)
        bad_id = pairs[0][1].prompt_id
        responses[bad_id].status = "error"
        comparisons = BiasScorer().evaluate_batch_pairs(pairs, responses)
        self.assertEqual(len(comparisons), len(pairs) - 1)

    def test_statistics_mark_zero_variance_degenerate(self):
        from types import SimpleNamespace
        comps = [SimpleNamespace(
            demographic_axis="gender", demographic_group="male", baseline_group="ref",
            sentiment_delta=0.0, score_base=80.0, score_perturbed=80.0,
            sentiment_base=0.2, sentiment_perturbed=0.2,
            decision_matches=True, score_delta=0.0, embedding_cosine_similarity=1.0,
        ) for _ in range(3)]
        result = StatisticalTestingEngine().analyze_comparisons(comps)
        self.assertEqual(result[0].status, "degenerate")
        self.assertIsNone(result[0].permutation_p_value)

    def test_controls_and_mock_error_mode(self):
        engine = PerturbationEngine()
        prompts, pairs = engine.generate_counterfactual_dataset(template_ids=["job_swe_001"], names_per_group=1)
        controls = [v for _, v in pairs if v.metadata.get("condition") in {"IDENTICAL", "SHAM"}]
        self.assertEqual({p.metadata["condition"] for p in controls}, {"IDENTICAL", "SHAM"})
        identical = next(p for p in controls if p.metadata["condition"] == "IDENTICAL")
        base = next(b for b, v in pairs if v is identical)
        self.assertEqual(base.rendered_prompt, identical.rendered_prompt)
        failing = QueryOrchestrator(MockLLMProvider(error_rate=1.0)).execute_batch(prompts)
        self.assertTrue(all(response.status == "error" for response in failing.values()))
        self.assertEqual(BiasScorer().evaluate_batch_pairs(pairs, failing), [])
        with self.assertRaises(RuntimeError):
            QueryOrchestrator.assert_acceptable_response_rate(failing)

    def test_mixed_effects_failure_reports_fallback(self):
        result = StatisticalTestingEngine.fit_mixed_effects([])
        self.assertEqual(result["status"], "fallback_permutation")

    def test_power_analysis_helper(self):
        n = StatisticalTestingEngine.estimate_paired_sample_size(0.5)
        self.assertGreater(n, 1)

    def test_stage5_end_to_end_audit_and_export(self):
        """Test full 5-stage pipeline integration."""
        engine = PerturbationEngine()
        all_prompts, pairs = engine.generate_counterfactual_dataset(
            template_ids=["job_swe_001"], names_per_group=1
        )
        provider = MockLLMProvider()
        orchestrator = QueryOrchestrator(provider=provider, cache=self.cache)
        responses = orchestrator.execute_batch(all_prompts)

        scorer = BiasScorer()
        comparisons = scorer.evaluate_batch_pairs(pairs, responses)
        self.assertEqual(len(comparisons), len(pairs))

        stats_engine = StatisticalTestingEngine()
        results = stats_engine.analyze_comparisons(comparisons)
        self.assertGreater(len(results), 0)

        # Test LaTeX table export
        latex = ReportGenerator.generate_latex_table(results)
        self.assertIn(r"\begin{table*}", latex)
        self.assertIn(r"\end{tabular}", latex)

    def test_gemini_provider_missing_key(self):
        """Test that GeminiProvider raises ValueError when API key is missing."""
        import os
        old_gemini = os.environ.pop("GEMINI_API_KEY", None)
        try:
            provider = GeminiProvider(api_key=None)
            with self.assertRaises(ValueError):
                provider.generate_response("Hello", "System prompt", "p_test")
        finally:
            if old_gemini:
                os.environ["GEMINI_API_KEY"] = old_gemini

    @patch("urllib.request.urlopen")
    def test_gemini_provider_mocked_response(self, mock_urlopen):
        """Test GeminiProvider parsing and ModelResponse creation from mocked Google Gemini endpoint."""
        fake_api_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Applicant Evaluation:\nApplicant meets all criteria.\n[DECISION: ACCEPT]\n[SCORE: 95/100]"
                            }
                        ],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                    "index": 0,
                }
            ],
            "usageMetadata": {"promptTokenCount": 45, "candidatesTokenCount": 25, "totalTokenCount": 70},
        }

        mock_resp_obj = MagicMock()
        mock_resp_obj.read.return_value = json.dumps(fake_api_response).encode("utf-8")
        mock_resp_obj.__enter__.return_value = mock_resp_obj
        mock_urlopen.return_value = mock_resp_obj

        provider = GeminiProvider(model_name="gemini-3.8-flash", api_key="AIzaSyTestDummyKey")
        resp = provider.generate_response(
            prompt_text="Evaluate applicant David Smith with 95 score.",
            system_prompt="You are an evaluator.",
            prompt_id="p_gemini_001",
        )

        self.assertEqual(resp.provider, "gemini")
        self.assertEqual(resp.model_name, "gemini-3.8-flash")
        self.assertEqual(resp.extracted_decision, "ACCEPT")
        self.assertEqual(resp.extracted_score, 95.0)
        self.assertIn("[DECISION: ACCEPT]", resp.raw_text)
        self.assertGreaterEqual(resp.latency_ms, 0.0)

    def test_gemini_orchestrator_config(self):
        """Test QueryOrchestrator factory properly instantiates GeminiProvider."""
        config = PromptBenchConfig()
        config.provider.provider_name = "gemini"
        config.provider.model_name = "gemini-3.8-flash"

        orchestrator = QueryOrchestrator.from_config(config)
        self.assertIsInstance(orchestrator.provider, GeminiProvider)
        self.assertEqual(orchestrator.provider.model_name, "gemini-3.8-flash")


if __name__ == "__main__":
    unittest.main()
