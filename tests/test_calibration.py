"""Regression checks for controlled variants, calibration and inferential units."""
import tempfile
import json
import unittest
from dataclasses import replace
from pathlib import Path

from promptbench.core.cache import ResponseCache
from promptbench.metrics.scorer import BiasScorer
from promptbench.metrics.decision_consistency import DecisionConsistencyScorer
from promptbench.metrics.sentiment import SentimentScorer
from promptbench.metrics.embeddings import CosineEmbeddingScorer
from promptbench.perturbation.engine import PerturbationEngine
from promptbench.query_pipeline.orchestrator import QueryOrchestrator
from promptbench.query_pipeline.providers.base import BaseLLMProvider
from promptbench.query_pipeline.providers.mock_provider import MockLLMProvider
from promptbench.query_pipeline.providers.gemini_provider import GeminiProvider
from promptbench.statistical_testing.engine import StatisticalTestingEngine
from promptbench.statistical_testing.permutation import PermutationTest
from promptbench.reporting.dataset_exporter import DatasetExporter


class CountingProvider(MockLLMProvider):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def generate_response(self, *args, **kwargs):
        self.calls += 1
        return super().generate_response(*args, **kwargs)


class TestCalibration(unittest.TestCase):
    def dataset(self, samples=2):
        return PerturbationEngine().generate_counterfactual_dataset(["job_swe_001"], samples)

    def comparisons(self):
        prompts, pairs = self.dataset()
        responses = QueryOrchestrator(MockLLMProvider()).execute_batch(prompts)
        return BiasScorer().evaluate_batch_pairs(pairs, responses)

    def test_only_intended_profile_fields_change(self):
        _, pairs = self.dataset()
        permitted = {
            "NAME": {"profile_id", "name"},
            "SES": {"profile_id", "ses_level", "education_institution", "residence_neighborhood", "extracurricular_cue"},
        }
        for base, variant in pairs:
            before, after = base.demographic_profile.to_dict(), variant.demographic_profile.to_dict()
            changed = {key for key in before if before[key] != after[key]}
            condition = variant.metadata["condition"]
            if condition in permitted:
                self.assertTrue(changed <= permitted[condition], (condition, changed))
            elif condition == "EXPLICIT":
                allowed = {"profile_id", "nationality"} if variant.metadata["axis"] == "nationality" else {"profile_id", "gender", "pronoun_subject", "pronoun_object", "pronoun_possessive"}
                self.assertTrue(changed <= allowed)
            else:
                self.assertEqual(changed, set())
        self.assertEqual(len({p.prompt_id for p in self.dataset()[0]}), len(self.dataset()[0]))

    def test_identical_replicates_are_fresh_provider_calls(self):
        prompts, _ = self.dataset(2)
        baseline = prompts[0]
        controls = [p for p in prompts if p.metadata.get("condition") == "IDENTICAL"]
        self.assertEqual(len(controls), 2)
        self.assertTrue(all(p.rendered_prompt == baseline.rendered_prompt for p in controls))
        with tempfile.TemporaryDirectory() as directory:
            cache = ResponseCache(Path(directory))
            provider = CountingProvider()
            orchestrator = QueryOrchestrator(provider, cache)
            for _ in range(2):
                results = orchestrator.execute_batch([baseline] + controls)
                self.assertTrue(all(not r.cache_hit for r in results.values()))
            self.assertEqual(provider.calls, 6)

    def test_cached_response_has_current_prompt_id(self):
        prompts, _ = self.dataset(1)
        baseline = replace(prompts[0], metadata={})
        repeat = replace(baseline, prompt_id="new_id")
        with tempfile.TemporaryDirectory() as directory:
            provider = CountingProvider()
            query = QueryOrchestrator(provider, ResponseCache(Path(directory)))
            query.execute_batch([baseline])
            response = query.execute_batch([repeat])["new_id"]
            self.assertTrue(response.cache_hit)
            self.assertEqual(response.prompt_id, "new_id")
            self.assertEqual(provider.calls, 1)

    def test_unparsed_decisions_are_missing_and_failures_excluded(self):
        prompts, pairs = self.dataset(1)
        responses = QueryOrchestrator(MockLLMProvider()).execute_batch(prompts)
        base, variant = pairs[0]
        responses[variant.prompt_id] = replace(responses[variant.prompt_id], extracted_decision=None)
        self.assertIsNone(BiasScorer().evaluate_batch_pairs([pairs[0]], responses)[0].decision_matches)
        responses[variant.prompt_id] = replace(responses[variant.prompt_id], extracted_decision="ERROR", metadata={"error": "unavailable"})
        self.assertEqual(BiasScorer().evaluate_batch_pairs([pairs[0]], responses), [])
        rates = DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact({"unknown": [None, "ERROR"], "valid": ["ACCEPT"]})
        self.assertNotIn("unknown", rates["selection_rates"])
        self.assertIsNone(rates["disparate_impact_ratio"])

    def test_template_count_not_number_of_names_is_inference_n(self):
        comps = self.comparisons()
        results = StatisticalTestingEngine().analyze_comparisons(comps)
        self.assertTrue(results)
        for result in results:
            self.assertEqual(result.sample_size, 1)
            self.assertEqual(result.bootstrap_ci_95, [None, None])
            self.assertFalse(result.is_significant_fdr)
        self.assertTrue(any(r.observation_count > r.sample_size for r in results))
        references = {r.calibration_reference for r in results if r.condition == "NAME"}
        self.assertEqual(references, {"baseline", "IDENTICAL", "SHAM"})

    def test_control_adjustment_and_same_metric_effect_size(self):
        comparison = self.comparisons()[0]
        rows = []
        for index, (treatment, control) in enumerate([(1.0, 0.25), (2.0, 0.5), (3.0, 0.75)]):
            template = f"template_{index}"
            rows.append(replace(comparison, template_id=template, condition="NAME", demographic_axis="ethnicity", demographic_group="Name cue", sentiment_delta=treatment, sentiment_base=0.0, sentiment_perturbed=treatment, score_base=80, score_perturbed=80, score_delta=0))
            rows.append(replace(comparison, template_id=template, condition="IDENTICAL", demographic_axis="control", demographic_group="Identical", sentiment_delta=control, sentiment_base=0.0, sentiment_perturbed=control))
        results = StatisticalTestingEngine().analyze_comparisons(rows)
        result = next(r for r in results if r.condition == "NAME" and r.metric_tested == "Sentiment delta" and r.calibration_reference == "IDENTICAL")
        self.assertEqual(result.sample_size, 3)
        self.assertEqual(result.observed_difference, 1.5)
        self.assertEqual(result.effect_size_cohens_d, 2.0)

    def test_small_sample_sign_flip_is_exact(self):
        _, p, _ = PermutationTest(resamples=1000).test_paired_differences([1.0] * 4)
        self.assertEqual(p, 0.125)

    def test_parser_rejects_arbitrary_prose_and_invalid_scores(self):
        self.assertEqual(BaseLLMProvider.parse_decision_and_score("Do not hire: the applicant is not approved."), (None, None))
        self.assertEqual(BaseLLMProvider.parse_decision_and_score("[DECISION: REJECT] [SCORE: 104/100]"), ("REJECT", None))
        self.assertEqual(BaseLLMProvider.parse_decision_and_score("[DECISION: APPROVED] [SCORE: 8/10]"), ("APPROVED", 80.0))
        self.assertEqual(BaseLLMProvider.parse_decision_and_score("[DECISION: ACCEPT / REJECT / INTERVIEW] [SCORE: 0-100]"), (None, None))

    def test_gemini_model_id_preserved(self):
        self.assertEqual(GeminiProvider(model_name="gemini-2.5-flash", api_key="test").model_name, "gemini-2.5-flash")

    def test_instrument_only_smoke_validation(self):
        # These exercise the instrument without making any model API requests.
        sentiment = SentimentScorer()
        self.assertGreater(sentiment.score_text("The applicant is qualified."), 0)
        self.assertLess(sentiment.score_text("The applicant is not qualified."), 0)
        cosine = CosineEmbeddingScorer()
        self.assertEqual(cosine.compute_similarity("Candidate is qualified.", "Candidate is qualified."), 1)
        self.assertEqual(cosine.compute_similarity("apple orchard", "rocket launch"), 0)
        self.assertEqual(sentiment.compute_sentiment_delta("solid performance", "solid performance")[2], 0)

    def test_exports_minimize_raw_text_and_retain_provenance(self):
        comparison = self.comparisons()[0]
        record = DatasetExporter.comparison_record(comparison)
        self.assertNotIn("base_response_text", record)
        self.assertNotIn("perturbed_prompt_text", record)
        self.assertEqual(record["condition"], comparison.condition)
        self.assertEqual(len(record["base_provenance"]["prompt_sha256"]), 64)
        self.assertEqual(record["base_provenance"]["model_name"], comparison.base_response.model_name)
        self.assertIn("finish_reason", record["base_provenance"])
        private = DatasetExporter.comparison_record(comparison, include_raw_text=True)
        self.assertEqual(private["base_response_text"], comparison.base_response.raw_text)
        self.assertEqual(private["base_prompt_text"], comparison.base_prompt.rendered_prompt)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"
            DatasetExporter.export_to_csv([], path)
            self.assertIn("condition", path.read_text())
            path = Path(directory) / "metrics.jsonl"
            DatasetExporter.export_to_jsonl([comparison], path)
            self.assertNotIn("base_response_text", json.loads(path.read_text()))

    def test_mock_does_not_treat_committee_as_mit_or_rewrite_ds_facts(self):
        response = MockLLMProvider().generate_response(
            "A talent evaluation committee reviews a Lead Data Scientist with causal inference experience.", "Evaluator", "ds"
        )
        self.assertNotIn("exceptionally prestigious", response.raw_text)
        self.assertIn("5 years", response.raw_text)
        self.assertNotIn("6 years", response.raw_text)

    def test_invalid_generation_arguments(self):
        with self.assertRaises(ValueError):
            PerturbationEngine().generate_counterfactual_dataset(["unknown"])
        with self.assertRaises(ValueError):
            self.dataset(0)


if __name__ == "__main__":
    unittest.main()
