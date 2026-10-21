"""Interrupted runs retain each original control call and reject changed experiments."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from promptbench.cli import main
from promptbench.perturbation.engine import PerturbationEngine
from promptbench.query_pipeline.checkpoint import AuditCheckpoint
from promptbench.query_pipeline.providers.mock_provider import MockLLMProvider


class TestAuditCheckpoint(unittest.TestCase):
    def test_completed_controls_resume_without_provider_replay(self):
        prompts, _ = PerturbationEngine().generate_counterfactual_dataset(["job_swe_001"], 1)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = AuditCheckpoint(directory, prompts, {"seed": 42})
            provider = MockLLMProvider()
            for prompt in prompts:
                checkpoint.record(provider.generate_response(prompt.rendered_prompt, prompt.system_prompt, prompt.prompt_id))
            recovered = AuditCheckpoint(directory, prompts, {"seed": 42}, resume=True)
            self.assertEqual(len(recovered.responses), len(prompts))
            controls = [p for p in prompts if p.metadata["condition"] in {"IDENTICAL", "SHAM"}]
            self.assertTrue(controls)
            for prompt in controls:
                self.assertEqual(recovered.responses[prompt.prompt_id].response_id, checkpoint.responses[prompt.prompt_id].response_id)
                self.assertFalse(recovered.responses[prompt.prompt_id].cache_hit)
            with self.assertRaisesRegex(ValueError, "differ"):
                AuditCheckpoint(directory, prompts, {"seed": 43}, resume=True)
            with self.assertRaisesRegex(ValueError, "already contains"):
                AuditCheckpoint(directory, prompts, {"seed": 42})

    def test_partial_last_record_does_not_lose_completed_records(self):
        prompts, _ = PerturbationEngine().generate_counterfactual_dataset(["job_swe_001"], 1)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = AuditCheckpoint(directory, prompts, {})
            p = prompts[0]
            checkpoint.record(MockLLMProvider().generate_response(p.rendered_prompt, p.system_prompt, p.prompt_id))
            with checkpoint.responses_path.open("ab") as stream:
                stream.write(b'{"prompt_id":')
            recovered = AuditCheckpoint(directory, prompts, {}, resume=True)
            self.assertEqual(list(recovered.responses), [p.prompt_id])
            self.assertEqual(checkpoint.responses_path.stat().st_mode & 0o777, 0o600)

    def test_cli_interrupted_and_resumed_run_calls_only_pending_prompts(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ["promptbench", "audit", "--provider", "mock", "--samples-per-group", "1", "--output-dir", directory]
            original = MockLLMProvider.generate_response
            calls = []
            def interrupted(provider, *args, **kwargs):
                if len(calls) == 3:
                    raise KeyboardInterrupt
                calls.append(kwargs["prompt_id"])
                return original(provider, *args, **kwargs)
            with patch("sys.argv", argv), patch.object(MockLLMProvider, "generate_response", interrupted), redirect_stdout(StringIO()):
                with self.assertRaises(KeyboardInterrupt):
                    main()
            self.assertEqual(len(Path(directory, "responses.private.jsonl").read_text().splitlines()), 3)
            recovered_calls = []
            def remaining(provider, *args, **kwargs):
                recovered_calls.append(kwargs["prompt_id"])
                return original(provider, *args, **kwargs)
            with patch("sys.argv", argv + ["--resume"]), patch.object(MockLLMProvider, "generate_response", remaining), redirect_stdout(StringIO()):
                main()
            self.assertFalse(set(calls) & set(recovered_calls))
            self.assertEqual(len(calls) + len(recovered_calls), 21)
            exported = json.loads(Path(directory, "audit_dataset.json").read_text())
            self.assertEqual(exported["summary"]["axis_summaries"]["run_execution"]["recovered_responses"], 3)
            self.assertEqual(len(exported["comparisons"]), 20)

    def test_brief_profile_and_template_subset_are_checkpointed(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ["promptbench", "audit", "--provider", "mock", "--template-ids", "job_swe_001", "loan_sb_001", "--brief-output", "--samples-per-group", "1", "--output-dir", directory]
            original = MockLLMProvider.generate_response
            system_prompts = []
            def provider_call(provider, *args, **kwargs):
                system_prompts.append(kwargs["system_prompt"])
                return original(provider, *args, **kwargs)
            with patch("sys.argv", argv), patch.object(MockLLMProvider, "generate_response", provider_call), redirect_stdout(StringIO()):
                main()
            manifest = json.loads(Path(directory, "run_manifest.json").read_text())
            self.assertEqual(manifest["planned_requests"], 42)
            self.assertEqual(manifest["settings"]["response_profile"], "brief_25_words_v1")
            self.assertTrue(all("Choose exactly one decision" in text for text in system_prompts))
            exported = json.loads(Path(directory, "audit_dataset.json").read_text())
            self.assertEqual(exported["summary"]["scenario_category"], "job_application + loan_eligibility")
